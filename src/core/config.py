"""Configuration management for the Endoscope AI project."""

import json
from pathlib import Path
from typing import Dict, List
from datetime import date, timedelta
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence

def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print("Config file not found: %s", config_path)
            print("Using default configuration with sample data")
            return Config.create_default()
            
        with open(config_file, "r", encoding="utf-8") as f:
            raw_cfg = json.load(f)
        
        # Validate required fields
        required_fields = ["min_abstract_lead_time_days", "min_paper_lead_time_days", 
                          "max_concurrent_submissions", "data_files"]
        for field in required_fields:
            if field not in raw_cfg:
                raise ValueError(f"Missing required field in config: {field}")
        
        config_dir = config_file.parent
        
        # Load conferences
        conferences_path = config_dir / raw_cfg["data_files"]["conferences"]
        if not conferences_path.exists():
            raise FileNotFoundError(f"Conferences file not found: {conferences_path}")
        conferences = _load_conferences(conferences_path)
        
        # Load submissions
        mods_path = config_dir / raw_cfg["data_files"]["mods"]
        papers_path = config_dir / raw_cfg["data_files"]["papers"]
        
        if not mods_path.exists():
            raise FileNotFoundError(f"Mods file not found: {mods_path}")
        if not papers_path.exists():
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
                blackout_path = config_dir / blackouts_rel
                if blackout_path.exists():
                    blackout_dates = _load_blackout_dates(blackout_path)
                else:
                    print("Warning: Blackout file not found: %s", blackout_path)
        
        return Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=raw_cfg["min_abstract_lead_time_days"],
            min_paper_lead_time_days=raw_cfg["min_paper_lead_time_days"],
            max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
            default_paper_lead_time_months=raw_cfg.get("default_paper_lead_time_months", 3),
            work_item_duration_days=raw_cfg.get("work_item_duration_days", 14),
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

def _load_blackout_dates(path: Path) -> List[date]:
    """Load blackout dates from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        blackout_dates = []
        
        # Add recurring holidays if available
        if "recurring_holidays" in raw:
            blackout_dates.extend(_load_recurring_holidays(raw["recurring_holidays"]))
        
        # Add federal holidays from year-specific data (fallback)
        current_year = date.today().year
        for year_key in [f"federal_holidays_{current_year}", f"federal_holidays_{current_year + 1}"]:
            if year_key in raw:
                for date_str in raw[year_key]:
                    try:
                        blackout_dates.append(parse_date(date_str).date())
                    except (ValueError, TypeError):
                        continue
        
        # Add custom blackout periods
        if "custom_blackout_periods" in raw:
            for period in raw["custom_blackout_periods"]:
                try:
                    start = parse_date(period["start"]).date()
                    end = parse_date(period["end"]).date()
                    current = start
                    while current <= end:
                        blackout_dates.append(current)
                        current += relativedelta(days=1)
                except (ValueError, TypeError):
                    continue
        
        return blackout_dates
    except Exception as e:
        print("Warning: Could not load blackout dates: %s", e)
        return []

def _load_recurring_holidays(recurring_holidays: List[Dict]) -> List[date]:
    """Load recurring holidays and generate dates for the next few years."""
    blackout_dates = []
    current_year = date.today().year
    
    # Generate dates for current year and next 2 years
    for year in range(current_year, current_year + 3):
        for holiday in recurring_holidays:
            try:
                holiday_date = date(year, holiday['month'], holiday['day'])
                blackout_dates.append(holiday_date)
            except ValueError:
                # Skip invalid dates (like Feb 29 in non-leap years)
                continue
    
    return blackout_dates

def _load_conferences(path: Path) -> List[Conference]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out: List[Conference] = []
    for c in raw:
        deadlines: Dict[SubmissionType, date] = {}
        if c.get("abstract_deadline"):
            try:
                deadlines[SubmissionType.ABSTRACT] = parse_date(c["abstract_deadline"]).date()
            except (ValueError, TypeError):
                continue
        if c.get("full_paper_deadline"):
            try:
                deadlines[SubmissionType.PAPER] = parse_date(c["full_paper_deadline"]).date()
            except (ValueError, TypeError):
                continue
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
    mods_path: Path,
    papers_path: Path,
    conferences: List[Conference],
    abs_lead: int,
    pap_lead: int,
    penalty_costs: Dict[str, float],
) -> List[Submission]:
    from datetime import date
    """Load submissions from mods and papers files."""
    with open(mods_path, "r", encoding="utf-8") as f:
        mods = json.load(f)
    with open(papers_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    submissions: List[Submission] = []
    conf_type_map = {c.id: c.conf_type for c in conferences}

    # Load mods as abstracts (work items)
    for mod in mods:
        mod_id = mod.get("id")
        if not mod_id:
            continue
        
        # Mods (work items) don't have conference assignments
        # They are internal development items
        conf_id = None
        
        # Determine engineering flag based on candidate conferences
        engineering = False
        candidate_conferences = mod.get("candidate_conferences", [])
        if candidate_conferences:
            # Check if any conference family is engineering
            has_engineering = any(family in conf_type_map and conf_type_map[family] == ConferenceType.ENGINEERING 
                               for family in candidate_conferences)
            has_medical = any(family in conf_type_map and conf_type_map[family] == ConferenceType.MEDICAL 
                            for family in candidate_conferences)
            # If it can go to engineering conferences, it's engineering
            engineering = has_engineering
        
        submissions.append(
            Submission(
                id=f"{mod_id}-wrk",
                title=mod.get("title", f"Mod {mod_id}"),
                kind=SubmissionType.ABSTRACT,
                conference_id=conf_id,  # None for work items
                depends_on=mod.get("depends_on", []),
                draft_window_months=mod.get("draft_window_months", 0),
                lead_time_from_parents=mod.get("lead_time_from_parents", 0),
                penalty_cost_per_day=penalty_costs.get("default_mod_penalty_per_day", 0.0),
                engineering=engineering,
                earliest_start_date=parse_date(mod.get("est_data_ready", date.today().isoformat())).date(),
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
        
        # Papers have candidate_conferences as suggestions, not assignments
        # We'll leave conference_id as None for now - it can be assigned later
        conf_id = None
        candidate_conferences = paper.get("candidate_conferences", [])
        
        # Determine engineering flag based on candidate conferences
        engineering = False
        if candidate_conferences:
            # Check if any candidate conference is engineering
            has_engineering = any(conf in conf_type_map and conf_type_map[conf] == ConferenceType.ENGINEERING 
                               for conf in candidate_conferences)
            has_medical = any(conf in conf_type_map and conf_type_map[conf] == ConferenceType.MEDICAL 
                            for conf in candidate_conferences)
            # If it can go to engineering conferences, it's engineering
            engineering = has_engineering
        
        # Calculate earliest start date - use provided date or calculate from conference deadlines
        provided_earliest_date = paper.get("earliest_start_date")
        if provided_earliest_date:
            earliest_start_date = parse_date(provided_earliest_date).date()
        else:
            # If no explicit date provided, calculate based on conference deadlines
            earliest_start_date = None
        
        # If we have candidate conferences, try to calculate a better earliest start date
        if candidate_conferences:
            # Find the earliest deadline among compatible conferences
            earliest_deadline = None
            for conf in conferences:
                if conf.name in candidate_conferences and SubmissionType.PAPER in conf.deadlines:
                    deadline = conf.deadlines[SubmissionType.PAPER]
                    if earliest_deadline is None or deadline < earliest_deadline:
                        earliest_deadline = deadline
            
            # If we found a deadline, calculate the latest start date needed
            if earliest_deadline:
                draft_window_months = paper.get("draft_window_months", 3)
                duration_days = draft_window_months * 30  # Approximate
                latest_start = earliest_deadline - timedelta(days=duration_days)
                # Use the calculated start date, or the provided date if it's earlier
                if earliest_start_date is None:
                    earliest_start_date = latest_start
                else:
                    earliest_start_date = min(earliest_start_date, latest_start)
        
        # If we still don't have an earliest start date, use a reasonable default
        if earliest_start_date is None:
            # Use current date as a reasonable starting point
            earliest_start_date = date.today()
        
        # Create submissions for each compatible conference
        for conf in conferences:
            if conf.name not in candidate_conferences:
                continue
            
            # Check if conference requires abstracts
            has_abstract_deadline = SubmissionType.ABSTRACT in conf.deadlines
            has_paper_deadline = SubmissionType.PAPER in conf.deadlines
            
            # Create abstract submission if conference requires it
            if has_abstract_deadline:
                abstract_id = f"{paper_id}-abs-{conf.id}"
                submissions.append(
                    Submission(
                        id=abstract_id,
                        title=f"Abstract for {paper.get('title', f'Paper {paper_id}')}",
                        kind=SubmissionType.ABSTRACT,
                        conference_id=conf.id,
                        depends_on=mod_deps + parent_deps,  # Abstract depends on mods and parent papers
                        draft_window_months=0,  # Abstracts are quick
                        lead_time_from_parents=paper.get("lead_time_from_parents", abs_lead),
                        penalty_cost_per_day=penalty_costs.get("default_mod_penalty_per_day", 0.0),
                        engineering=engineering,
                        earliest_start_date=earliest_start_date,
                        candidate_conferences=[conf.name],  # Specific to this conference
                    )
                )
            
            # Create paper submission if conference requires it
            if has_paper_deadline:
                paper_id_suffix = f"{paper_id}-pap-{conf.id}"
                
                # Paper depends on abstract if conference requires both
                paper_dependencies = mod_deps + parent_deps
                if has_abstract_deadline:
                    abstract_dep_id = f"{paper_id}-abs-{conf.id}"
                    paper_dependencies.append(abstract_dep_id)
                
                submissions.append(
                    Submission(
                        id=paper_id_suffix,
                        title=paper.get("title", f"Paper {paper_id}"),
                        kind=SubmissionType.PAPER,
                        conference_id=conf.id,
                        depends_on=paper_dependencies,
                        draft_window_months=paper.get("draft_window_months", 3),
                        lead_time_from_parents=paper.get("lead_time_from_parents", pap_lead),
                        penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                        engineering=engineering,
                        earliest_start_date=earliest_start_date,
                        candidate_conferences=[conf.name],  # Specific to this conference
                    )
                )
        
        # If no conferences were compatible, create a generic paper submission
        if not candidate_conferences or not any(conf.name in candidate_conferences for conf in conferences):
            submissions.append(
                Submission(
                    id=f"{paper_id}-pap",
                    title=paper.get("title", f"Paper {paper_id}"),
                    kind=SubmissionType.PAPER,
                    conference_id=conf_id,  # None initially - can be assigned later
                    depends_on=mod_deps + parent_deps,
                    draft_window_months=paper.get("draft_window_months", 3),
                    lead_time_from_parents=paper.get("lead_time_from_parents", pap_lead),
                    penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                    engineering=engineering,
                    earliest_start_date=earliest_start_date,
                    candidate_conferences=candidate_conferences,  # Set the candidate conferences
                )
            )

    return submissions


def save_config(config: Config, config_path: str) -> None:
    """Save a Config object to a JSON file."""
    try:
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert config to dictionary
        config_dict = {
            "min_abstract_lead_time_days": config.min_abstract_lead_time_days,
            "min_paper_lead_time_days": config.min_paper_lead_time_days,
            "max_concurrent_submissions": config.max_concurrent_submissions,
            "default_paper_lead_time_months": config.default_paper_lead_time_months,
            "work_item_duration_days": config.work_item_duration_days,
            "penalty_costs": config.penalty_costs or {},
            "priority_weights": config.priority_weights or {},
            "scheduling_options": config.scheduling_options or {},
            "blackout_dates": [d.isoformat() for d in (config.blackout_dates or [])],
            "data_files": config.data_files or {}
        }
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        raise RuntimeError(f"Failed to save configuration: {e}")

 