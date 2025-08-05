"""Configuration loading and parsing."""

from __future__ import annotations
import json
import os
from typing import Dict, List, Optional, Any
from datetime import date
from .models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
from .dates import parse_date_safe
from dateutil.relativedelta import relativedelta

def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, "r", encoding="utf-8") as f:
            raw_cfg = json.load(f)
        
        # Validate required fields
        required_fields = ["min_abstract_lead_time_days", "min_paper_lead_time_days", 
                          "max_concurrent_submissions", "data_files"]
        for field in required_fields:
            if field not in raw_cfg:
                raise ValueError(f"Missing required field in config: {field}")
        
        config_dir = os.path.dirname(os.path.abspath(config_path))
        
        # Load conferences
        conferences_path = os.path.join(config_dir, raw_cfg["data_files"]["conferences"])
        if not os.path.exists(conferences_path):
            raise FileNotFoundError(f"Conferences file not found: {conferences_path}")
        conferences = _load_conferences(conferences_path)
        
        # Load submissions
        mods_path = os.path.join(config_dir, raw_cfg["data_files"]["mods"])
        papers_path = os.path.join(config_dir, raw_cfg["data_files"]["papers"])
        
        if not os.path.exists(mods_path):
            raise FileNotFoundError(f"Mods file not found: {mods_path}")
        if not os.path.exists(papers_path):
            raise FileNotFoundError(f"Papers file not found: {papers_path}")
            
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
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
                if os.path.exists(blackout_path):
                    blackout_dates = _load_blackout_dates(blackout_path)
                else:
                    print(f"Warning: Blackout file not found: {blackout_path}")
        
        return Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=raw_cfg["min_abstract_lead_time_days"],
            min_paper_lead_time_days=raw_cfg["min_paper_lead_time_days"],
            max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
            default_paper_lead_time_months=raw_cfg.get("default_paper_lead_time_months", 3),
            penalty_costs=raw_cfg.get("penalty_costs", {"default_mod_penalty_per_day": 1000}),
            priority_weights=raw_cfg.get(
                "priority_weights",
                {
                    "engineering_paper": 2.0,
                    "medical_paper": 1.0,
                    "mod": 1.5,
                    "abstract": 0.5,
                },
            ),
            scheduling_options=raw_cfg.get("scheduling_options", {}),
            blackout_dates=blackout_dates,
            data_files=raw_cfg["data_files"],
        )
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file error: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in configuration: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")

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
                    blackout_dates.append(parse_date_safe(date_str))
        # Add custom blackout periods
        if "custom_blackout_periods" in raw:
            for period in raw["custom_blackout_periods"]:
                start = parse_date_safe(period["start"])
                end = parse_date_safe(period["end"])
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
            deadlines[SubmissionType.ABSTRACT] = parse_date_safe(c["abstract_deadline"])
        if c.get("full_paper_deadline"):
            deadlines[SubmissionType.PAPER] = parse_date_safe(c["full_paper_deadline"])
        out.append(
            Conference(
                id=c["name"],
                name=c["name"],
                conf_type=ConferenceType(c["conference_type"]),
                recurrence=ConferenceRecurrence(c["recurrence"]),
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
    conf_type_map = {c.id: c.conf_type for c in conferences}
    conf_family_map = {}
    for c in conferences:
        # Build a mapping from family/type to conference IDs
        conf_family_map.setdefault(str(c.conf_type), []).append(c.id)

    # Load mods as abstracts
    for mod in mods:
        mod_id = mod.get("id") or mod.get("mod_id")
        if not mod_id:
            continue
        conf_id = mod.get("conference_id")
        # If not set, try to map by family
        if not conf_id and mod.get("conference_families"):
            for fam in mod["conference_families"]:
                if fam in conf_family_map:
                    conf_id = conf_family_map[fam][0]  # Pick the first match
                    break
        # Set engineering flag based on conference type if not set
        engineering = mod.get("engineering")
        if engineering is None and conf_id in conf_type_map:
            engineering = conf_type_map[conf_id] == ConferenceType.ENGINEERING
        submissions.append(
            Submission(
                id=f"{mod_id}-wrk",
                title=mod.get("title", f"Mod {mod_id}"),
                kind=SubmissionType.ABSTRACT,
                conference_id=conf_id,
                depends_on=mod.get("depends_on", []),
                draft_window_months=mod.get("draft_window_months", 0),
                lead_time_from_parents=mod.get("lead_time_from_parents", 0),
                penalty_cost_per_day=penalty_costs.get("default_mod_penalty_per_day", 0.0),
                engineering=engineering if engineering is not None else False,
                earliest_start_date=parse_date_safe(mod.get("est_data_ready", "2025-01-01")),
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
        conf_id = paper.get("conference_id")
        # If not set, try to map by family
        if not conf_id and paper.get("conference_families"):
            for fam in paper["conference_families"]:
                if fam in conf_family_map:
                    conf_id = conf_family_map[fam][0]  # Pick the first match
                    break
        # Set engineering flag based on conference type if not set
        engineering = paper.get("engineering")
        if engineering is None and conf_id in conf_type_map:
            engineering = conf_type_map[conf_id] == ConferenceType.ENGINEERING
        submissions.append(
            Submission(
                id=f"{paper_id}-pap",
                title=paper.get("title", f"Paper {paper_id}"),
                kind=SubmissionType.PAPER,
                conference_id=conf_id,
                depends_on=mod_deps + parent_deps,
                draft_window_months=paper.get("draft_window_months", 3),
                lead_time_from_parents=paper.get("lead_time_from_parents", 0),
                penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                engineering=engineering if engineering is not None else False,
                earliest_start_date=parse_date_safe(paper.get("earliest_start_date", "2025-01-01")),
            )
        )

    return submissions

 