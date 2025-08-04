import pytest
import os
import sys

# ensure src folder on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from planner import Planner
from datetime import datetime
from core.dates import parse_date_safe

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