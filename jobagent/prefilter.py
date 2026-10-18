"""Cheap, deterministic filtering and ranking before any AI sees the jobs."""

import re

REMOTE_WORDS = ["remote", "distans", "på distans", "hemifrån", "hemarbete", "work from home", "fully remote"]
HYBRID_WORDS = ["hybrid", "hybridarbete", "flexibel arbetsplats"]


def _contains(text, words):
    text = text.lower()
    return any(re.search(rf"\b{re.escape(w.lower())}\b", text) for w in words if w)


def work_mode(job):
    """'remote', 'hybrid' or '' (unknown / on-site), guessed from the ad text."""
    text = f"{job['title']} {job['description']}"
    if _contains(text, REMOTE_WORDS):
        return "remote"
    if _contains(text, HYBRID_WORDS):
        return "hybrid"
    return ""


def location_ok(job, cfg):
    places = [p.lower() for p in cfg["location"]["places"]]
    if not places:
        return True
    if cfg["location"]["include_remote"] and job["work_mode"] == "remote":
        return True
    where = f"{job['municipality']} {job['region']}".lower()
    return any(p in where for p in places)


def title_ok(job, cfg):
    title = job["title"].lower()
    must = [w.lower() for w in cfg["filters"]["title_must_contain_any"]]
    exclude = [w.lower() for w in cfg["filters"]["title_exclude"]]
    if must and not any(w in title for w in must):
        return False
    return not any(w in title for w in exclude)


def keyword_score(job, cfg):
    """0-100 rough relevance from query + boost words; only used to order jobs before AI scoring."""
    title = job["title"].lower()
    description = job["description"].lower()
    score = 0
    for query in cfg["search"]["queries"]:
        if query.lower() in title:
            score += 40
            break
    for word in cfg["filters"]["boost_keywords"]:
        w = word.lower()
        score += 15 if w in title else 5 if w in description else 0
    if job["work_mode"]:
        score += 10
    return min(score, 100)


def prefilter(jobs, cfg):
    kept = []
    for job in jobs:
        job = {**job, "work_mode": work_mode(job)}
        if title_ok(job, cfg) and location_ok(job, cfg):
            job["keyword_score"] = keyword_score(job, cfg)
            kept.append(job)
    kept.sort(key=lambda j: (j["keyword_score"], j["posted"]), reverse=True)
    return kept
