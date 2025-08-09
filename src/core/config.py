"""Configuration management for the Endoscope AI project."""

import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dateutil.parser import parse as parse_date

from src.core.models import (
    Conference, ConferenceRecurrence, ConferenceType, ConferenceSubmissionType, Config, Submission, 
    SubmissionType, SubmissionWorkflow
)
from src.core.constants import SCHEDULING_CONSTANTS, PENALTY_CONSTANTS

# Regex patterns for robust ID matching
MOD_ID_PATTERN = re.compile(r'^mod_(\d+)$')
PAPER_ID_PATTERN = re.compile(r'^(.+)-pap-(.+)$')
ABSTRACT_ID_PATTERN = re.compile(r'^(.+)-abs-(.+)$')

def normalize_conference_id(conference_name: str) -> str:
    """Normalize conference ID to lowercase with underscores."""
    return conference_name.lower().replace('-', '_').replace(' ', '_')

def find_mod_by_number(submissions: List[Submission], mod_number: int) -> Optional[Submission]:
    """Find mod submission by number."""
    expected_id = f"mod_{mod_number}"
    return next((s for s in submissions if s.id == expected_id), None)

def find_paper_by_base_and_conference(submissions: List[Submission], base_id: str, conference_id: str) -> Optional[Submission]:
    """Find paper submission by base ID and conference."""
    normalized_conf = normalize_conference_id(conference_id)
    expected_id = f"{base_id}-pap-{normalized_conf}"
    return next((s for s in submissions if s.id == expected_id), None)


def _map_conference_data(json_data: Dict) -> Dict:
    """Map JSON conference data to model fields."""
    # Normalize conference ID for consistency
    conference_id = normalize_conference_id(json_data["name"])
    
    return {
        "id": conference_id,
        "name": json_data["name"],
        "conf_type": ConferenceType(json_data.get("conference_type", "MEDICAL")),
        "recurrence": ConferenceRecurrence(json_data.get("recurrence", "annual")),
        "deadlines": _build_deadlines_dict(json_data),
        "submission_types": ConferenceSubmissionType(json_data.get("submission_types")) if json_data.get("submission_types") else None
    }


def _parse_candidate_kinds(json_data: Dict) -> Optional[List[SubmissionType]]:
    """Parse candidate_kinds from JSON."""
    if json_data.get("candidate_kinds"):
        return [SubmissionType(t) for t in json_data["candidate_kinds"]]
    else:
        return None


def _parse_submission_workflow(json_data: Dict) -> Optional[SubmissionWorkflow]:
    """Parse submission workflow from JSON data."""
    workflow = json_data.get('submission_workflow')
    if workflow:
        return SubmissionWorkflow(workflow)
    else:
        return None


def _build_deadlines_dict(conf_data: Dict) -> Dict[SubmissionType, date]:
    """Build deadlines dict from JSON data."""
    deadlines = {}
    if conf_data.get("full_paper_deadline"):
        deadlines[SubmissionType.PAPER] = parse_date(conf_data["full_paper_deadline"]).date()
    if conf_data.get("abstract_deadline"):
        deadlines[SubmissionType.ABSTRACT] = parse_date(conf_data["abstract_deadline"]).date()
    return deadlines


def _map_paper_data(json_data: Dict) -> Dict:
    """Map JSON paper data to model fields."""
    # Get depends_on directly (already consolidated)
    depends_on = json_data.get("depends_on", [])
    
    # Parse author field
    author = json_data.get("author", "ed")
    
    return {
        "id": json_data["id"],
        "title": json_data["title"],
        "kind": SubmissionType.PAPER,
        "author": author,  # Explicit author field
        "conference_id": None,  # Will be assigned later
        "depends_on": depends_on if depends_on else None,
        "draft_window_months": json_data.get("draft_window_months", 3),
        "lead_time_from_parents": json_data.get("lead_time_from_parents", 0),
        "candidate_conferences": json_data.get("candidate_conferences", []),
        "candidate_kinds": _parse_candidate_kinds(json_data),  # Preferred submission types
        "submission_workflow": _parse_submission_workflow(json_data),  # How this submission should be handled
        # Unified schema fields
        "engineering_ready_date": parse_date(json_data["engineering_ready_date"]).date() if json_data.get("engineering_ready_date") else None,
        "free_slack_months": json_data.get("free_slack_months", 1),
        "penalty_cost_per_month": json_data.get("penalty_cost_per_month", PENALTY_CONSTANTS.default_mod_penalty_per_day * SCHEDULING_CONSTANTS.days_per_month)
    }


def _map_mod_data(json_data: Dict) -> Dict:
    """Map JSON mod data to model fields."""
    engineering_ready_date = None
    if json_data.get("engineering_ready_date"):
        engineering_ready_date = parse_date(json_data["engineering_ready_date"]).date()
    
    # Parse author field
    author = json_data.get("author", "pccp")
    
    return {
        "id": json_data['id'],  # Use ID as-is from JSON (already has mod_ prefix)
        "title": json_data["title"],
        "kind": SubmissionType.PAPER,  # Mods are papers (PCCP research papers)
        "author": author,  # Explicit author field
        "conference_id": None,  # No pre-assigned conference
        "candidate_conferences": json_data.get("candidate_conferences", []),  # Map candidate conferences
        "candidate_kinds": _parse_candidate_kinds(json_data),  # Preferred submission types
        "submission_workflow": _parse_submission_workflow(json_data),  # How this submission should be handled
        "depends_on": json_data.get("depends_on", []),
        "draft_window_months": json_data.get("draft_window_months", 2),  # Use actual draft window
        "lead_time_from_parents": json_data.get("lead_time_from_parents", 0),
        "penalty_cost_per_day": json_data.get("penalty_cost_per_month", PENALTY_CONSTANTS.default_mod_penalty_per_day * SCHEDULING_CONSTANTS.days_per_month) / SCHEDULING_CONSTANTS.days_per_month,
        "engineering": json_data.get("engineering", False),
        "earliest_start_date": engineering_ready_date,
        # Unified schema fields
        "engineering_ready_date": engineering_ready_date,
        "free_slack_months": json_data.get("free_slack_months"),
        "penalty_cost_per_month": json_data.get("penalty_cost_per_month")
    }


def load_config(config_path: str) -> Config:
    """Load configuration from JSON file."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Configuration file not found: {config_path}")
            print("Using default configuration with sample data")
            return Config.create_default()
        
        print(f"DEBUG: Loading config from {config_path}")
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Load data files - use config file directory as base
        config_dir = config_file.parent
        data_files = config_data.get("data_files", {})
        conferences_path = config_dir / data_files.get("conferences", "data/conferences.json")
        mods_path = config_dir / data_files.get("mods", "data/mods.json")
        papers_path = config_dir / data_files.get("papers", "data/papers.json")
        blackouts_path = config_dir / data_files.get("blackouts", "data/blackout.json")
        
        print("DEBUG: Data file paths:")
        print(f"  Conferences: {conferences_path} (exists: {conferences_path.exists()})")
        print(f"  Mods: {mods_path} (exists: {mods_path.exists()})")
        print(f"  Papers: {papers_path} (exists: {papers_path.exists()})")
        
        # Load conferences with proper field mapping
        conferences = _load_conferences(conferences_path)
        print(f"DEBUG: Loaded {len(conferences)} conferences")
        
        # Load submissions with proper abstract-paper dependencies
        submissions = _load_submissions_with_abstracts(
            mods_path, papers_path, conferences, config_data
        )
        print(f"DEBUG: Loaded {len(submissions)} submissions")
        
        # Load blackout dates only if enabled
        scheduling_options = config_data.get("scheduling_options", {})
        enable_blackout_periods = scheduling_options.get("enable_blackout_periods", False)
        
        if enable_blackout_periods:
            blackout_dates = _load_blackout_dates(blackouts_path)
        else:
            blackout_dates = []
        
        # Create config object
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=config_data.get("min_abstract_lead_time_days", SCHEDULING_CONSTANTS.min_abstract_lead_time_days),
            min_paper_lead_time_days=config_data.get("min_paper_lead_time_days", SCHEDULING_CONSTANTS.min_paper_lead_time_days),
            max_concurrent_submissions=config_data.get("max_concurrent_submissions", SCHEDULING_CONSTANTS.max_concurrent_submissions),
            default_paper_lead_time_months=config_data.get("default_paper_lead_time_months", SCHEDULING_CONSTANTS.default_paper_lead_time_months),
            work_item_duration_days=config_data.get("work_item_duration_days", SCHEDULING_CONSTANTS.work_item_duration_days),
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
        
        # Load federal holidays (new format)
        for year in [2025, 2026]:
            federal_holidays_key = f"federal_holidays_{year}"
            if federal_holidays_key in data:
                for date_str in data[federal_holidays_key]:
                    try:
                        blackout_dates.append(parse_date(date_str).date())
                    except (ValueError, TypeError):
                        continue
        
        # Load custom blackout periods
        custom_periods = data.get("custom_blackout_periods", [])
        for period in custom_periods:
            try:
                start_date = parse_date(period["start"]).date()
                end_date = parse_date(period["end"]).date()
                current_date = start_date
                while current_date <= end_date:
                    blackout_dates.append(current_date)
                    current_date += timedelta(days=1)
            except (KeyError, ValueError, TypeError):
                continue
        
        # Load recurring holidays (old format)
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
    """Load conferences from JSON file with proper field mapping."""
    conferences = []
    
    if not path.exists():
        return conferences
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for conf_data in data:
            try:
                # Use the mapping function to transform JSON data to model fields
                mapped_data = _map_conference_data(conf_data)
                conference = Conference(**mapped_data)
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
    """Load submissions without creating combinatorial explosions.
    
    This creates only the necessary base submissions:
    - Work items (mods) as-is
    - Papers as-is (without conference-specific variants)
    
    Conference assignment happens during scheduling, not during loading.
    """
    submissions = []
    
    # Load penalty costs
    penalty_costs = config_data.get("penalty_costs", {})
    
    # Create a map of conference names for validation
    conference_names = {conf.name for conf in conferences}
    
    # Load both mods and papers - both need conference validation now
    mods = _load_mods(mods_path)
    papers = _load_papers(papers_path)
    
    # Process all submissions (mods + papers) uniformly
    all_submissions = mods + papers
    for submission_data in all_submissions:
        # Validate candidate conferences exist
        valid_candidates = []
        if hasattr(submission_data, 'candidate_conferences') and submission_data.candidate_conferences:
            for conf_name in submission_data.candidate_conferences:
                if conf_name in conference_names:
                    valid_candidates.append(conf_name)
                else:
                    print(f"Warning: {submission_data.id} references unknown conference: {conf_name}")
        
        # Determine submission type and properties
        if hasattr(submission_data, 'kind'):
            # Already a Submission object (from mods), just validate conferences
            submission_data.candidate_conferences = valid_candidates
            submissions.append(submission_data)
        else:
            # Paper object - create Submission
            paper_submission = Submission(
                id=submission_data.id,  # Keep original ID
                title=submission_data.title,
                kind=SubmissionType.PAPER,
                conference_id=None,  # Will be assigned by scheduler
                depends_on=submission_data.depends_on.copy() if submission_data.depends_on else [],
                draft_window_months=submission_data.draft_window_months,
                lead_time_from_parents=submission_data.lead_time_from_parents,
                penalty_cost_per_day=penalty_costs.get("default_paper_penalty_per_day", 0.0),
                engineering=submission_data.engineering,
                earliest_start_date=submission_data.earliest_start_date,
                candidate_conferences=valid_candidates  # Only valid conferences
            )
            submissions.append(paper_submission)
    
    print(f"Created {len(submissions)} total submissions: {len(mods)} mods + {len(papers)} papers")
    
    return submissions


def _load_mods(path: Path) -> List[Submission]:
    """Load mods from JSON file with proper field mapping."""
    mods = []
    
    if not path.exists():
        return mods
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for mod_data in data:
            try:
                # Use the mapping function to transform JSON data to model fields
                mapped_data = _map_mod_data(mod_data)
                mod = Submission(**mapped_data)
                mods.append(mod)
                
            except (KeyError, ValueError) as e:
                print(f"Warning: Could not load mod {mod_data.get('id', 'unknown')}: {e}")
                continue
                
    except Exception as e:
        print(f"Warning: Could not load mods from {path}: {e}")
    
    return mods


def _load_papers(path: Path) -> List[Submission]:
    """Load papers from JSON file with proper field mapping."""
    papers = []
    
    if not path.exists():
        return papers
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for paper_data in data:
            try:
                # Use the mapping function to transform JSON data to model fields
                mapped_data = _map_paper_data(paper_data)
                paper = Submission(**mapped_data)
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
        raise RuntimeError(f"Failed to save configuration: {e}") from e

 