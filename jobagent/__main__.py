"""Command line used by the GitHub workflows and by AI agents.

    python -m jobagent fetch [days]        fetch new ads → data/inbox/<today>.json, report → data/last-run.md
    python -m jobagent pending             list inbox dates that have no scores yet
    python -m jobagent validate <date>     check data/scored/<date>.json
    python -m jobagent render <date>       print the issue body for that date
    python -m jobagent preview [days]      dry run: what config.yaml would catch over the last N days (default 14)
    python -m jobagent suggest <word>...   real occupation/skill terms used in Platsbanken ads (for search terms)
    python -m jobagent fingerprint         short hash of config.yaml (matches "Config:" in data/last-run.md)
"""

import json
import re
import sys

from . import config as c
from .digest import render_scored, render_unscored
from .fetch import fetch_jobs, suggest_terms
from .prefilter import prefilter
from .schema import validate_scored

SEEN_RETENTION_DAYS = 90
PENDING_DAYS = 7


def _read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _place(job):
    return job["municipality"] or job["region"] or "?"


def run_report(found, kept, days):
    """Plain-text summary of one search, shared by `preview` (printed) and `fetch` (saved for remote AIs)."""
    kept_ids = {j["id"] for j in kept}
    dropped = [j for j in found if j["id"] not in kept_ids]
    lines = [
        f"Last {days} days: {len(found)} ads found, {len(kept)} kept, {len(dropped)} dropped by filters",
        f"(about {len(kept) / int(days):.1f} new jobs per day)",
        "",
        "KEPT:",
        *[f"  {j['keyword_score']:>3}  {j['title']} — {j['company']} ({_place(j)})" for j in kept],
        "",
        "DROPPED (first 25):",
        *[f"       {j['title']} — {j['company']} ({_place(j)})" for j in dropped[:25]],
    ]
    return "\n".join(lines) + "\n"


def config_fingerprint():
    """Lets an AI in a sandbox tell whether data/last-run.md was produced from the config it just pushed."""
    import hashlib

    return hashlib.sha256((c.ROOT / "config.yaml").read_bytes()).hexdigest()[:12]


def cmd_fetch(days=None):
    from datetime import date, datetime, timedelta
    from zoneinfo import ZoneInfo

    cfg, day = c.load_config(), c.today()
    if days:
        cfg["search"]["published_within_days"] = int(days)
    seen = _read(c.SEEN, {})
    found = fetch_jobs(cfg, today=day)
    fresh = [j for j in found if j["id"] not in seen]
    kept = prefilter(fresh, cfg)
    print(f"{len(fresh)} unseen ads, {len(kept)} kept after filters")

    # Remember everything we looked at, so filtered-out ads don't come back tomorrow either
    for job in fresh:
        seen[job["id"]] = day
    cutoff = (date.fromisoformat(day) - timedelta(days=SEEN_RETENTION_DAYS)).isoformat()
    _write(c.SEEN, {k: v for k, v in sorted(seen.items()) if v >= cutoff})

    now = datetime.now(ZoneInfo("Europe/Stockholm")).isoformat(timespec="seconds")
    report = run_report(fresh, kept, cfg["search"]["published_within_days"])
    (c.DATA / "last-run.md").write_text(
        f"Run: {now}\nConfig: {config_fingerprint()}\n(only ads not seen in earlier runs are counted)\n\n{report}",
        encoding="utf-8")

    if kept:
        path = c.INBOX / f"{day}.json"
        inbox = _read(path, {"date": day, "jobs": []})
        inbox["jobs"] += kept
        _write(path, inbox)
        print(f"wrote {path.relative_to(c.ROOT)}")


def cmd_preview(days="14"):
    """Dry run for tuning config.yaml: writes nothing, shows what would be kept and dropped."""
    cfg = c.load_config()
    cfg["search"]["published_within_days"] = int(days)
    found = fetch_jobs(cfg, today=c.today())
    print("\n" + run_report(found, prefilter(found, cfg), days), end="")


def cmd_fingerprint():
    print(config_fingerprint())


def cmd_suggest(*words):
    """Helps an AI pick search terms that actually occur in Swedish ads, for any occupation."""
    if not words:
        sys.exit("usage: python -m jobagent suggest <word> [<word>...]")
    for word in words:
        print(f"\n{word}:")
        for term in suggest_terms(word):
            print(f"  {term['occurrences']:>5}  {term['value']}  ({term['type']})")


def cmd_pending():
    from datetime import date, timedelta

    # Older unscored days aren't worth an AI run; the keyword-ranked issue already covers them
    cutoff = (date.fromisoformat(c.today()) - timedelta(days=PENDING_DAYS)).isoformat()
    for path in sorted(c.INBOX.glob("*.json")):
        if path.stem >= cutoff and not (c.SCORED / path.name).exists():
            print(path.stem)


def cmd_validate(day):
    inbox = _read(c.INBOX / f"{day}.json")
    scored = _read(c.SCORED / f"{day}.json")
    if inbox is None or scored is None:
        sys.exit(f"missing data/inbox/{day}.json or data/scored/{day}.json")
    errors = validate_scored(scored, inbox)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"ok: {len(scored['jobs'])} of {len(inbox['jobs'])} jobs scored")


def cmd_render(day):
    cfg = c.load_config()
    inbox = _read(c.INBOX / f"{day}.json")
    if inbox is None:
        sys.exit(f"missing data/inbox/{day}.json")
    scored = _read(c.SCORED / f"{day}.json")
    if scored is not None and not validate_scored(scored, inbox):
        sys.stdout.write(render_scored(inbox, scored, cfg))
    else:
        sys.stdout.write(render_unscored(inbox, cfg))


def main(argv):
    commands = {"fetch": cmd_fetch, "pending": cmd_pending, "validate": cmd_validate, "render": cmd_render,
                "preview": cmd_preview, "suggest": cmd_suggest, "fingerprint": cmd_fingerprint}
    if not argv or argv[0] not in commands:
        sys.exit(__doc__)
    if argv[0] in ("preview", "fetch") and argv[1:] and not argv[1].isdigit():
        sys.exit(f"expected a number of days, got {argv[1]!r}")
    if argv[0] in ("validate", "render") and argv[1:] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", argv[1]):
        sys.exit(f"expected a date like 2026-10-18, got {argv[1]!r}")
    commands[argv[0]](*argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
