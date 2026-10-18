"""Renders the daily GitHub Issue body: keyword-ranked before AI scoring, AI-ranked after."""

import re

MARKER = "<!-- job-agent:{date} -->"


def safe(text, limit=300):
    """Job ads are untrusted: flatten to one line, stop @-mentions, links, and HTML."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = text.replace("@", "@​").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"([\[\]`*_|#])", r"\\\1", text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def safe_url(url):
    return url if re.match(r"^https://[^\s()<>]+$", url or "") else ""


def _heading(n, job):
    title = safe(job["title"], 120)
    url = safe_url(job["link"])
    linked = f"[{title}]({url})" if url else title
    return f"### {n}. {linked} — {safe(job['company'], 80)}"


def _facts(job):
    where = job["municipality"] or job["region"] or "Location not given"
    parts = [safe(where, 60)]
    if job.get("work_mode"):
        parts.append(job["work_mode"])
    if job.get("employment_type"):
        parts.append(safe(job["employment_type"], 40))
    parts.append(f"posted {job['posted']}" if job["posted"] else "")
    if job.get("deadline"):
        parts.append(f"apply by {job['deadline']}")
    return " · ".join(p for p in parts if p)


def render_unscored(inbox, cfg):
    jobs = inbox["jobs"][: cfg["digest"]["max_jobs"]]
    lines = [
        MARKER.format(date=inbox["date"]),
        f"**{len(inbox['jobs'])} new job(s)** matched your filters. Not AI-scored yet — ordered by keyword match.",
        "",
        "> To score them against `profile.md`, ask Claude or Codex: **“Score today's jobs”** "
        "(see the README). This issue updates itself when scores arrive.",
        "",
    ]
    for n, job in enumerate(jobs, 1):
        lines += [_heading(n, job), _facts(job), ""]
    if len(inbox["jobs"]) > len(jobs):
        lines.append(f"_…and {len(inbox['jobs']) - len(jobs)} more in `data/inbox/{inbox['date']}.json`._")
    return "\n".join(lines).rstrip() + "\n"


BADGE = {"apply": "✅ apply", "maybe": "🤔 maybe", "skip": "⏭️ skip"}


def render_scored(inbox, scored, cfg):
    by_id = {j["id"]: j for j in inbox["jobs"]}
    rows = [{**by_id[s["id"]], **s} for s in scored["jobs"] if s["id"] in by_id]
    rows.sort(key=lambda r: r["score"], reverse=True)
    min_score = cfg["digest"]["min_ai_score"]
    top = [r for r in rows if r["score"] >= min_score and r["recommendation"] != "skip"][: cfg["digest"]["max_jobs"]]
    rest = [r for r in rows if r not in top]
    unscored = len(by_id) - len(rows)

    lines = [
        MARKER.format(date=inbox["date"]),
        f"**{len(top)} worth a look** out of {len(by_id)} new job(s), scored against your profile"
        f" by {safe(scored.get('scored_by') or 'AI', 40)}.",
        "",
    ]
    if not top:
        lines += ["_Nothing cleared the bar today._", ""]
    for n, r in enumerate(top, 1):
        lines += [
            f"{_heading(n, r)} · **{r['score']}** {BADGE[r['recommendation']]}",
            _facts(r),
            "",
            f"> {safe(r['summary'], 500)}",
            "",
            f"**Why:** {safe(r['reasoning'], 500)}",
        ]
        if r.get("concerns"):
            lines.append(f"**Watch out:** {safe('; '.join(r['concerns']), 300)}")
        lines.append("")
    if rest:
        lines += [f"<details><summary>{len(rest)} filtered out</summary>", ""]
        lines += [f"- {r['score']} · {safe(r['title'], 100)} — {safe(r['company'], 60)}" for r in rest]
        lines += ["", "</details>", ""]
    if unscored:
        lines.append(f"_{unscored} job(s) were not scored._")
    return "\n".join(lines).rstrip() + "\n"
