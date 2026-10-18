import json
from pathlib import Path

import pytest

from jobagent.config import DEFAULTS
from jobagent.digest import render_scored, render_unscored, safe
from jobagent.fetch import normalize
from jobagent.prefilter import prefilter
from jobagent.schema import validate_scored

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "jobtech_search.json").read_text())


@pytest.fixture
def cfg():
    cfg = {k: dict(v) for k, v in DEFAULTS.items()}
    cfg["search"]["queries"] = ["product manager", "produktchef", "product owner"]
    cfg["location"]["places"] = ["Stockholm"]
    cfg["filters"]["title_must_contain_any"] = ["product", "produkt"]
    cfg["filters"]["title_exclude"] = ["marketing"]
    cfg["filters"]["boost_keywords"] = ["senior", "saas"]
    return cfg


@pytest.fixture
def jobs():
    return [normalize(h) for h in FIXTURE["hits"]]


def test_normalize_prefers_platsbanken_link_and_keeps_apply_link(jobs):
    job = jobs[0]
    assert job["id"] == "1001"
    assert job["link"].startswith("https://arbetsformedlingen.se/")
    assert job["apply_link"] == "https://example.com/apply/1001"
    assert job["posted"] == "2026-10-16" and job["deadline"] == "2026-11-15"


def test_prefilter_applies_title_and_location_rules(cfg, jobs):
    kept = {j["id"]: j for j in prefilter(jobs, cfg)}
    assert "1002" not in kept  # excluded title word
    assert "1004" not in kept  # Göteborg, on-site
    assert kept["1003"]["work_mode"] == "remote"  # outside Stockholm but remote
    assert kept["1001"]["work_mode"] == "hybrid"
    assert prefilter(jobs, cfg)[0]["id"] == "1001"  # senior + saas ranks first


def test_remote_jobs_dropped_when_not_wanted(cfg, jobs):
    cfg["location"]["include_remote"] = False
    assert "1003" not in {j["id"] for j in prefilter(jobs, cfg)}


def test_empty_places_means_all_of_sweden(cfg, jobs):
    cfg["location"]["places"] = []
    assert "1004" in {j["id"] for j in prefilter(jobs, cfg)}


def _inbox(cfg, jobs):
    return {"date": "2026-10-18", "jobs": prefilter(jobs, cfg)}


def _scored(**overrides):
    job = {"id": "1001", "score": 88, "recommendation": "apply", "summary": "Owns the platform.",
           "reasoning": "Senior B2B SaaS role in Stockholm.", "concerns": []}
    job.update(overrides)
    return {"date": "2026-10-18", "scored_by": "Claude", "jobs": [job]}


def test_schema_accepts_valid_and_rejects_bad(cfg, jobs):
    inbox = _inbox(cfg, jobs)
    assert validate_scored(_scored(), inbox) == []
    assert validate_scored(_scored(score="high"), inbox)
    assert validate_scored(_scored(score=101), inbox)
    assert validate_scored(_scored(recommendation="yes"), inbox)
    assert validate_scored(_scored(id="9999"), inbox)
    assert validate_scored(_scored(summary=""), inbox)
    assert validate_scored({"jobs": "nope"}, inbox)


def test_digests_render_and_neutralize_hostile_ads(cfg, jobs):
    inbox = _inbox(cfg, jobs)
    for body in (render_unscored(inbox, cfg), render_scored(inbox, _scored(), cfg)):
        assert "<!-- job-agent:2026-10-18 -->" in body
        assert "@everyone" not in body
        assert "javascript:" not in body
        assert "<b>" not in body
    scored_body = render_scored(inbox, _scored(), cfg)
    assert "**88** ✅ apply" in scored_body
    assert "not scored" in scored_body  # the other inbox jobs


def test_safe_escapes_markdown_links():
    assert "](" not in safe("[click](https://evil.example)").replace("\\]", "")


def test_suggest_keeps_only_occupation_and_skill_terms():
    from jobagent.fetch import suggest_terms

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"typeahead": [
                {"value": "sjuksköterska", "type": "occupation", "occurrences": 2050},
                {"value": "sjuksköterskelegitimation", "type": "skill", "occurrences": 42},
                {"value": "stockholm", "type": "location", "occurrences": 9000},
            ]}

    class FakeSession:
        def get(self, url, params, **kwargs):
            assert params["q"] == "sjuksköt"
            return FakeResponse()

    assert [t["value"] for t in suggest_terms("sjuksköt", session=FakeSession())] == [
        "sjuksköterska", "sjuksköterskelegitimation"]


def test_run_report_counts_and_lists(cfg, jobs):
    from jobagent.__main__ import run_report

    kept = prefilter(jobs, cfg)
    report = run_report(jobs, kept, 14)
    assert report.startswith(f"Last 14 days: {len(jobs)} ads found, {len(kept)} kept, {len(jobs) - len(kept)} dropped")
    assert "Senior Product Manager — Exempel AB (Stockholm)" in report.split("DROPPED")[0]
    assert "Product Marketing Manager" in report.split("DROPPED")[1]


def test_partially_scored_day_stays_pending(tmp_path, monkeypatch, cfg, jobs):
    import jobagent.__main__ as cli
    from jobagent import config as c

    monkeypatch.setattr(c, "INBOX", tmp_path / "inbox")
    monkeypatch.setattr(c, "SCORED", tmp_path / "scored")
    monkeypatch.setattr(c, "today", lambda: "2026-10-18")
    inbox = _inbox(cfg, jobs)
    cli._write(c.INBOX / "2026-10-18.json", inbox)
    cli._write(c.SCORED / "2026-10-18.json", _scored())  # only job 1001 scored
    remaining = {j["id"] for j in cli._unscored("2026-10-18")}
    assert remaining == {j["id"] for j in inbox["jobs"]} - {"1001"}
    cli._write(c.SCORED / "2026-10-18.json", {**_scored(), "jobs": [
        {**_scored()["jobs"][0], "id": j["id"]} for j in inbox["jobs"]]})
    assert cli._unscored("2026-10-18") == []
