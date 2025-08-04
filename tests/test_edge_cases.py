from datetime import datetime
from planner import Planner
import pytest
from core.dates import parse_date_safe

@pytest.fixture
def planner():
    return Planner(config_path="config.json")

def test_validate_config_runs(planner):
    # Should not raise
    planner.validate_config()

def test_abstract_before_full_each_year(planner):
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
    # ICCV appears only in odd years
    rows = planner.generate_monthly_table()
    iccv_instances = [r for r in rows if "ICCV" in r.get("Deadlines","")]
    for row in iccv_instances:
        year = int(row["Month"].split("-")[0])
        assert year % 2 == 1

def test_concurrency_limit(planner):
    rows = planner.generate_monthly_table()
    max_active = max(len(r["Active Papers"].split(", ")) if r["Active Papers"] else 0 for r in rows)
    assert max_active <= planner.config["max_concurrent_papers"]

def test_mod_paper_alignment(planner):
    mod_sched, paper_sched = planner.greedy_schedule()
    for p in planner.papers:
        pid = p["id"]
        for mid in p.get("mod_dependencies", []):
            assert paper_sched[pid] >= mod_sched[mid]

def test_parent_child_lead(planner):
    mod_sched, paper_sched = planner.greedy_schedule()
    for p in planner.papers:
        pid = p["id"]
        for par in p.get("parent_papers", []):
            par_end = paper_sched[par] + planner.papers_dict[par]["draft_window_months"]
            lead = p.get("lead_time_from_parents", planner.config["default_paper_lead_time_months"])
            assert paper_sched[pid] >= par_end + lead

