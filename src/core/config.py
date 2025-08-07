"""Configuration management for the Endoscope AI project."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from src.core.models import (
    Config, Submission, Conference, SubmissionType, ConferenceType, 
    ConferenceRecurrence, generate_abstract_id, create_abstract_submission,
    ensure_abstract_paper_dependency
)
# parse_date is already imported from dateutil.parser above


def load_config(config_path: str) -> Config:
    """Load configuration from JSON file."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Configuration file not found: %s {config_path}")
            print("Using default configuration with sample data")
            return Config.create_default()
        
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Load data files
        data_files = config_data.get("data_files", {})
        conferences_path = Path("data") / data_files.get("conferences", "conferences.json")
        mods_path = Path("data") / data_files.get("mods", "mods.json")
        papers_path = Path("data") / data_files.get("papers", "papers.json")
        blackouts_path = Path("data") / data_files.get("blackouts", "blackout.json")
        
        # Load conferences
        conferences = _load_conferences(conferences_path)
        
        # Load submissions with proper abstract-paper dependencies
        submissions = _load_submissions_with_abstracts(
            mods_path, papers_path, conferences, config_data
        )
        
        # Load blackout dates
        blackout_dates = _load_blackout_dates(blackouts_path)
        
        # Create config object
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=config_data.get("min_abstract_lead_time_days", 30),
            min_paper_lead_time_days=config_data.get("min_paper_lead_time_days", 90),
            max_concurrent_submissions=config_data.get("max_concurrent_submissions", 2),
            default_paper_lead_time_months=config_data.get("default_paper_lead_time_months", 3),
            work_item_duration_days=config_data.get("work_item_duration_days", 14),
            penalty_costs=config_data.get("penalty_costs", {}),
            priority_weights=config_data.get("priority_weights", {}),
            scheduling_options=config_data.get("scheduling_options", {}),
            blackout_dates=blackout_dates,
            data_files=data_files
        )
        
        return config
        
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {str(e)}")
        print("Using default configuration with sample data")
        return Config.create_default()


def _load_blackout_dates(path: Path) -> List[date]:
    """Load blackout dates from JSON file."""
    blackout_dates = []
    
    if not path.exists():
        return blackout_dates
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Load custom blackout dates
        custom_dates = data.get("custom_dates", [])
        for date_str in custom_dates:
            try:
                blackout_dates.append(parse_date(date_str).date())
            except (ValueError, TypeError):
                continue
        
        # Load recurring holidays
        recurring_holidays = data.get("recurring_holidays", [])
        holiday_dates = _load_recurring_holidays(recurring_holidays)
        blackout_dates.extend(holiday_dates)
        
    except Exception as e:
        print(f"Warning: Could not load blackout dates from {path}: {e}")
    
    return blackout_dates


def _load_recurring_holidays(recurring_holidays: List[Dict]) -> List[date]:
    """Load recurring holiday dates."""
    holiday_dates = []
    
    for holiday in recurring_holidays:
        try:
            month = holiday.get("month", 1)
            day = holiday.get("day", 1)
            year = holiday.get("year", 2025)
            
            # Add for multiple years
            for year_offset in range(-1, 3):  # Previous year to 2 years ahead
                holiday_date = date(year + year_offset, month, day)
                holiday_dates.append(holiday_date)
        except (ValueError, TypeError):
            continue
    
    return holiday_dates


def _load_conferences(path: Path) -> List[Conference]:
    """Load conferences from JSON file."""
    conferences = []
    
    if not path.exists():
        return conferences
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for conf_data in data:
            try:
                # Parse deadlines
                deadlines = {}
                if conf_data.get("abstract_deadline"):
                    deadlines[SubmissionType.ABSTRACT] = parse_date(conf_data["abstract_deadline"]).date()
                if conf_data.get("full_paper_deadline"):
                    deadlines[SubmissionType.PAPER] = parse_date(conf_data["full_paper_deadline"]).date()
                if conf_data.get("poster_deadline"):
                    deadlines[SubmissionType.POSTER] = parse_date(conf_data["poster_deadline"]).date()
                
                conference = Conference(
                    id=conf_data["name"],
                    name=conf_data["name"],
                    conf_type=ConferenceType(conf_data.get("conference_type", "ENGINEERING")),
                    recurrence=ConferenceRecurrence(conf_data.get("recurrence", "annual")),
                    deadlines=deadlines
                )
                conferences.append(conference)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not load conference {conf_data.get('name', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        print(f"Warning: Could not load conferences from {path}: {e}")
    
    return conferences


def _load_submissions_with_abstracts(
    mods_path: Path,
    papers_path: Path,
    conferences: List[Conference],
    config_data: Dict[str, Any]
) -> List[Submission]:
    """Load submissions and create proper abstract-paper dependencies."""
    submissions = []
    
    # Load penalty costs
    penalty_costs = config_data.get("penalty_costs", {})
    
    # Load mods (work items)
    mods = _load_mods(mods_path)
    submissions.extend(mods)
    
    # Load papers and create abstracts as needed
    papers = _load_papers(papers_path)
    
    for paper in papers:
        # Create submissions for each compatible conference
        for conf in conferences:
            if paper.candidate_conferences and conf.name not in paper.candidate_conferences:
                continue
            
            # Check if conference requires abstracts
            has_abstract_deadline = SubmissionType.ABSTRACT in conf.deadlines
            has_paper_deadline = SubmissionType.PAPER in conf.deadlines
            
            # Create abstract submission if conference requires it
            if has_abstract_deadline:
                abstract_submission = create_abstract_submission(paper, conf.id, penalty_costs)
                submissions.append(abstract_submission)
            
            # Create paper submission if conference requires it
            if has_paper_deadline:
                paper_id_suffix = f"{paper.id}-pap-{conf.id}"
                
                # Paper depends on abstract if conference requires both
                paper_dependencies = paper.depends_on.copy() if paper.depends_on else []
                if has_abstract_deadline:
                    abstract_id = generate_abstract_id(paper.id, conf.id)
                    paper_dependencies.append(abstract_id)
                
                paper_submission = Submission(
                    id=paper_id_suffix,
                    title=paper.title,
                    kind=SubmissionType.PAPER,
                    conference_id=conf.id,
                    depends_on=paper_dependencies,
                    draft_window_months=paper.draft_window_months,
                    lead_time_from_parents=paper.lead_time_from_parents,
                    penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                    engineering=paper.engineering,
                    earliest_start_date=paper.earliest_start_date,
                    candidate_conferences=[conf.name],  # Specific to this conference
                )
                submissions.append(paper_submission)
        
        # If no conferences were compatible, create a generic paper submission
        if not paper.candidate_conferences or not any(conf.name in paper.candidate_conferences for conf in conferences):
            generic_paper = Submission(
                id=f"{paper.id}-pap",
                title=paper.title,
                kind=SubmissionType.PAPER,
                conference_id=None,  # None initially - can be assigned later
                depends_on=paper.depends_on.copy() if paper.depends_on else [],
                draft_window_months=paper.draft_window_months,
                lead_time_from_parents=paper.lead_time_from_parents,
                penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                engineering=paper.engineering,
                earliest_start_date=paper.earliest_start_date,
                candidate_conferences=paper.candidate_conferences,
            )
            submissions.append(generic_paper)
    
    return submissions


def _load_mods(path: Path) -> List[Submission]:
    """Load mods (work items) from JSON file."""
    mods = []
    
    if not path.exists():
        return mods
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for mod_data in data:
            try:
                mod = Submission(
                    id=f"{mod_data['id']}-wrk",
                    title=mod_data.get("title", f"Mod {mod_data['id']}"),
                    kind=SubmissionType.ABSTRACT,  # Mods are work items (abstracts)
                    conference_id=None,  # Mods don't have conferences initially
                    depends_on=[],
                    draft_window_months=0,
                    lead_time_from_parents=0,
                    penalty_cost_per_day=0.0,
                    engineering=mod_data.get("engineering", False),
                    earliest_start_date=parse_date(mod_data.get("est_data_ready", "2025-06-01")).date() if mod_data.get("est_data_ready") else None,
                )
                mods.append(mod)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not load mod {mod_data.get('id', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        print(f"Warning: Could not load mods from {path}: {e}")
    
    return mods


def _load_papers(path: Path) -> List[Submission]:
    """Load papers from JSON file."""
    papers = []
    
    if not path.exists():
        return papers
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for paper_data in data:
            try:
                # Convert mod dependencies to submission IDs
                mod_deps = [f"{mod_id}-wrk" for mod_id in paper_data.get("mod_dependencies", [])]
                
                # Convert parent paper dependencies
                parent_deps = paper_data.get("parent_papers", [])
                
                # Combine all dependencies
                all_deps = mod_deps + parent_deps
                
                paper = Submission(
                    id=paper_data["id"],
                    title=paper_data.get("title", f"Paper {paper_data['id']}"),
                    kind=SubmissionType.PAPER,
                    conference_id=None,  # Will be assigned during config loading
                    depends_on=all_deps,
                    draft_window_months=paper_data.get("draft_window_months", 3),
                    lead_time_from_parents=paper_data.get("lead_time_from_parents", 0),
                    penalty_cost_per_day=paper_data.get("penalty_cost", 0.0),
                    engineering=paper_data.get("engineering", False),
                    earliest_start_date=None,  # Will be calculated based on dependencies
                    candidate_conferences=paper_data.get("candidate_conferences", []),
                )
                papers.append(paper)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not load paper {paper_data.get('id', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        print(f"Warning: Could not load papers from {path}: {e}")
    
    return papers


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

 