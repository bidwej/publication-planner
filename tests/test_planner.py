import pytest
import os

from src.planner import Planner
from src.core.dates import parse_date_safe

@pytest.fixture  # type: ignore
def planner():
    return Planner(config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json')))

def test_multi_parent(planner):
    mod_sched, paper_sched = planner.greedy_schedule()
    j2 = paper_sched["J2"]
    j3 = paper_sched["J3"]
    lead = planner.papers_dict["J3"].get("lead_time_from_parents",
                                         planner.config["default_paper_lead_time_months"])
    assert j3 >= j2 + planner.papers_dict["J2"]["draft_window_months"] + lead

def test_free_slack(planner):
    for m in planner.mods:
        assert m.get("free_slack_months", 0) >= 0

def test_biennial_conference(planner):
    # ICCV is biennial => odd years
    iccv = next(c for c in planner.config["conferences"] if c["name"] == "ICCV")
    deadline_date = parse_date_safe(iccv["full_paper_deadline"])
    year = deadline_date.year
    assert year % 2 == 1


def test_validate_config_runs(planner):
    """Test that config validation runs without errors."""
    # Should not raise
    planner.validate_config()


def test_abstract_before_full_each_year(planner):
    """Test that abstracts appear before full papers in each year."""
    rows = planner.generate_monthly_table()
    # For each conference with both deadlines in config
    for c in planner.config["conferences"]:
        a0 = c.get("abstract_deadline")
        f0 = c.get("full_paper_deadline")
        if not a0 or not f0:
            continue
        base_a = parse_date_safe(a0)
        base_f = parse_date_safe(f0)
        # Check month ordering within each year in table
        a_month = f"{base_a.year}-{base_a.month:02d}"
        f_month = f"{base_f.year}-{base_f.month:02d}"
        # Must appear and a_month <= f_month
        months = [r["Month"] for r in rows]
        assert a_month in months
        assert f_month in months
        # Compare full dates, not just month/day within same year
        assert base_a <= base_f


def test_biennial_iccv(planner):
    """Test that ICCV appears only in odd years."""
    rows = planner.generate_monthly_table()
    iccv_instances = [r for r in rows if "ICCV" in r.get("Deadlines","")]
    for row in iccv_instances:
        year = int(row["Month"].split("-")[0])
        assert year % 2 == 1


def test_concurrency_limit(planner):
    """Test that concurrency limit is respected."""
    rows = planner.generate_monthly_table()
    max_active = max(len(r["Active Papers"].split(", ")) if r["Active Papers"] else 0 for r in rows)
    assert max_active <= planner.config["max_concurrent_papers"]


def test_mod_paper_alignment(planner):
    """Test that MOD dependencies are respected for papers."""
    mod_sched, paper_sched = planner.greedy_schedule()
    for p in planner.papers:
        pid = p["id"]
        for mid in p.get("mod_dependencies", []):
            assert paper_sched[pid] >= mod_sched[mid]


def test_parent_child_lead(planner):
    """Test that parent-child lead times are respected."""
    mod_sched, paper_sched = planner.greedy_schedule()
    for p in planner.papers:
        pid = p["id"]
        for par in p.get("parent_papers", []):
            par_end = paper_sched[par] + planner.papers_dict[par]["draft_window_months"]
            lead = p.get("lead_time_from_parents", planner.config["default_paper_lead_time_months"])
            assert paper_sched[pid] >= par_end + lead