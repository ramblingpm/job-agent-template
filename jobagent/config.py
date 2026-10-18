"""Loads config.yaml and fills in defaults so a half-edited file still works."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INBOX = DATA / "inbox"
SCORED = DATA / "scored"
SEEN = DATA / "seen.json"

DEFAULTS = {
    "search": {"queries": [], "published_within_days": 3, "max_per_query": 100},
    "location": {"places": [], "include_remote": True},
    "filters": {"title_must_contain_any": [], "title_exclude": [], "boost_keywords": []},
    "digest": {"max_jobs": 30, "min_ai_score": 50},
}


def load_config(path=ROOT / "config.yaml"):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    cfg = {}
    for section, defaults in DEFAULTS.items():
        values = raw.get(section) or {}
        # YAML turns an emptied list into None; treat that as "use the default"
        cfg[section] = {k: values.get(k) if values.get(k) is not None else v for k, v in defaults.items()}
    if not cfg["search"]["queries"]:
        raise ValueError("config.yaml: add at least one entry under search.queries")
    return cfg


def today():
    """Today's date in Sweden, since that's where the jobs (and the user) are."""
    return datetime.now(ZoneInfo("Europe/Stockholm")).date().isoformat()
