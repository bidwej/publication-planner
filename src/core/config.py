from __future__ import annotations
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from dateutil.relativedelta import relativedelta
from .types import (
    Config,
    Conference,
    ConferenceType,
    Submission,
    SubmissionType,
)
from .dates import parse_date, parse_date_safe

def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = json.load(f)
    config_dir = os.path.dirname(os.path.abspath(config_path))
    conferences = _load_conferences(os.path.join(config_dir, raw_cfg["data_files"]["conferences"]))
    submissions = _load_submissions(
        mods_path=os.path.join(config_dir, raw_cfg["data_files"]["mods"]),
        papers_path=os.path.join(config_dir, raw_cfg["data_files"]["papers"]),
        conferences=conferences,
        abs_lead=raw_cfg["min_abstract_lead_time_days"],
        pap_lead=raw_cfg["min_paper_lead_time_days"],
        penalty_costs=raw_cfg.get("penalty_costs", {}),
    )
    # Load blackout dates if enabled
    blackout_dates = []
    if raw_cfg.get("scheduling_options", {}).get("enable_blackout_periods", False):
        blackouts_rel = raw_cfg["data_files"].get("blackouts")
        if blackouts_rel:
            blackout_path = os.path.join(config_dir, blackouts_rel)
            blackout_dates = _load_blackout_dates(blackout_path)
    return Config(
        min_abstract_lead_time_days=raw_cfg["min_abstract_lead_time_days"],
        min_paper_lead_time_days=raw_cfg["min_paper_lead_time_days"],
        max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
        default_paper_lead_time_months=raw_cfg.get("default_paper_lead_time_months", 3),
        conferences=conferences,
        submissions=submissions,
        data_files=raw_cfg["data_files"],
        priority_weights=raw_cfg.get(
            "priority_weights",
            {
                "engineering_paper": 2.0,
                "medical_paper": 1.0,
                "mod": 1.5,
                "abstract": 0.5,
            },
        ),
        penalty_costs=raw_cfg.get(
            "penalty_costs", {"default_mod_penalty_per_day": 1000}
        ),
        scheduling_options=raw_cfg.get("scheduling_options", {}),
        blackout_dates=blackout_dates,
    )

def _load_blackout_dates(path: str) -> List[date]:
    """Load blackout dates from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        blackout_dates = []
        # Add federal holidays
        for year_key in ["federal_holidays_2025", "federal_holidays_2026"]:
            if year_key in raw:
                for date_str in raw[year_key]:
                    blackout_dates.append(parse_date(date_str))
        # Add custom blackout periods
        if "custom_blackout_periods" in raw:
            for period in raw["custom_blackout_periods"]:
                start = parse_date(period["start"])
                end = parse_date(period["end"])
                current = start
                while current <= end:
                    blackout_dates.append(current)
                    current += relativedelta(days=1)
        return blackout_dates
    except Exception as e:
        print(f"Warning: Could not load blackout dates: {e}")
        return []

def _load_conferences(path: str) -> List[Conference]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out: List[Conference] = []
    for c in raw:
        deadlines: Dict[SubmissionType, date] = {}
        if c.get("abstract_deadline"):
            deadlines[SubmissionType.ABSTRACT] = parse_date(c["abstract_deadline"])
        if c.get("full_paper_deadline"):
            deadlines[SubmissionType.PAPER] = parse_date(c["full_paper_deadline"])
        out.append(
            Conference(
                id=c["name"],
                conf_type=ConferenceType(c["conference_type"]),
                recurrence=c["recurrence"],
                deadlines=deadlines,
            )
        )
    return out

def _load_submissions(
    mods_path: str,
    papers_path: str,
    conferences: List[Conference],
    abs_lead: int,
    pap_lead: int,
    penalty_costs: Dict[str, float],
) -> List[Submission]:
    """Load submissions from mods and papers files."""
    with open(mods_path, "r", encoding="utf-8") as f:
        mods = json.load(f)
    with open(papers_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    submissions: List[Submission] = []
    conf_map = {c.id: c for c in conferences}

    # Load mods as abstracts
    for mod in mods:
        mod_id = mod.get("id") or mod.get("mod_id")
        if not mod_id:
            continue
        submissions.append(
            Submission(
                id=f"{mod_id}-wrk",
                kind=SubmissionType.ABSTRACT,
                title=mod.get("title", f"Mod {mod_id}"),
                earliest_start_date=parse_date(mod.get("earliest_start_date", "2025-01-01")),
                conference_id=mod.get("conference_id"),
                engineering=mod.get("engineering", False),
                depends_on=mod.get("depends_on", []),
                penalty_cost_per_day=penalty_costs.get("default_mod_penalty_per_day", 0.0),
            )
        )

    # Load papers
    for paper in papers:
        paper_id = paper.get("id")
        if not paper_id:
            continue
        
        # Convert mod_dependencies to new submission IDs
        mod_deps = []
        for mod_id in paper.get("mod_dependencies", []):
            mod_deps.append(f"{mod_id}-wrk")
        
        # Convert parent_papers to new submission IDs
        parent_deps = []
        for parent_id in paper.get("parent_papers", []):
            parent_deps.append(f"{parent_id}-pap")
        
        submissions.append(
            Submission(
                id=f"{paper_id}-pap",
                kind=SubmissionType.PAPER,
                title=paper.get("title", f"Paper {paper_id}"),
                earliest_start_date=parse_date(paper.get("earliest_start_date", "2025-01-01")),
                conference_id=paper.get("conference_id"),
                engineering=paper.get("engineering", False),
                depends_on=mod_deps + parent_deps,
                penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                lead_time_from_parents=paper.get("lead_time_from_parents", 0),
                draft_window_months=paper.get("draft_window_months", 0),
            )
        )

    return submissions

 