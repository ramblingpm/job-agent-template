"""Validates the scored-jobs file the AI writes, so a bad run fails loudly instead of posting garbage."""

RECOMMENDATIONS = {"apply", "maybe", "skip"}


def validate_scored(scored, inbox):
    """Return a list of problems (empty list = valid). Missing jobs are allowed but reported."""
    errors = []
    if not isinstance(scored, dict) or not isinstance(scored.get("jobs"), list):
        return ["top level must be an object with a 'jobs' list"]
    if scored.get("date") != inbox.get("date"):
        errors.append(f"date {scored.get('date')!r} does not match inbox date {inbox.get('date')!r}")
    inbox_ids = {j["id"] for j in inbox.get("jobs", [])}
    seen = set()
    for i, job in enumerate(scored["jobs"]):
        where = f"jobs[{i}]"
        if not isinstance(job, dict):
            errors.append(f"{where}: must be an object")
            continue
        job_id = str(job.get("id", ""))
        if job_id not in inbox_ids:
            errors.append(f"{where}: id {job_id!r} is not in the inbox")
        if job_id in seen:
            errors.append(f"{where}: id {job_id!r} appears twice")
        seen.add(job_id)
        score = job.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            errors.append(f"{where}: score must be an integer 0-100")
        if job.get("recommendation") not in RECOMMENDATIONS:
            errors.append(f"{where}: recommendation must be one of {sorted(RECOMMENDATIONS)}")
        for field in ("summary", "reasoning"):
            if not isinstance(job.get(field), str) or not job[field].strip():
                errors.append(f"{where}: {field} must be a non-empty string")
        concerns = job.get("concerns", [])
        if not isinstance(concerns, list) or not all(isinstance(c, str) for c in concerns):
            errors.append(f"{where}: concerns must be a list of strings")
    return errors
