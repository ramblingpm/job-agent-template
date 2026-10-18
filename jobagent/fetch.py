"""Fetches ads from Platsbanken via the free JobTech search API (no key needed)."""

from datetime import date, timedelta

import requests

API_URL = "https://jobsearch.api.jobtechdev.se/search"
COMPLETE_URL = "https://jobsearch.api.jobtechdev.se/complete"
DESCRIPTION_CHARS = 1500


def normalize(hit):
    """Turn one JobTech API hit into the flat job dict the rest of the agent uses."""
    employer = hit.get("employer") or {}
    address = hit.get("workplace_address") or {}
    description = hit.get("description") or {}
    text = (description.get("text") or "") if isinstance(description, dict) else str(description)
    application_url = (hit.get("application_details") or {}).get("url")
    return {
        "id": str(hit["id"]),
        "title": hit.get("headline") or "Untitled",
        "company": employer.get("name") or employer.get("workplace") or "Unknown company",
        "municipality": address.get("municipality") or "",
        "region": address.get("region") or "",
        "link": hit.get("webpage_url") or application_url or "",
        "apply_link": application_url or "",
        "posted": (hit.get("publication_date") or "")[:10],
        "deadline": (hit.get("application_deadline") or "")[:10],
        "employment_type": (hit.get("employment_type") or {}).get("label") or "",
        "salary": hit.get("salary_description") or "",
        "description": text.strip()[:DESCRIPTION_CHARS],
    }


def fetch_jobs(cfg, session=None, today=None):
    """Run every configured query and return unique, normalized jobs."""
    session = session or requests.Session()
    today = date.fromisoformat(today) if today else date.today()
    since = today - timedelta(days=cfg["search"]["published_within_days"])
    jobs = {}
    for query in cfg["search"]["queries"]:
        params = {
            "q": query,
            "limit": min(int(cfg["search"]["max_per_query"]), 100),
            "published-after": f"{since.isoformat()}T00:00:00",
            "sort": "pubdate-desc",
        }
        response = session.get(API_URL, params=params, headers={"accept": "application/json"}, timeout=30)
        response.raise_for_status()
        hits = response.json().get("hits", [])
        print(f"'{query}': {len(hits)} ads")
        for hit in hits:
            if hit.get("removed"):
                continue
            job = normalize(hit)
            jobs.setdefault(job["id"], job)
    return list(jobs.values())


def suggest_terms(word, session=None, limit=15):
    """Typeahead from JobTech: occupation and skill words as they appear in current ads, with counts."""
    session = session or requests.Session()
    response = session.get(COMPLETE_URL, params={"q": word, "limit": limit}, headers={"accept": "application/json"}, timeout=30)
    response.raise_for_status()
    terms = response.json().get("typeahead", [])
    return [t for t in terms if t.get("type") in ("occupation", "skill")]
