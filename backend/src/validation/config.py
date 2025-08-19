"""Configuration validation functions for data integrity and schema compliance."""

from typing import Dict, Any, List
from datetime import date

from src.core.models import Config, Submission, Conference
from src.core.constants import SCHEDULING_CONSTANTS


def validate_config(config: Config) -> List[str]:
    """Validate complete configuration and return list of errors."""
    errors = []
    
    # Field validation
    errors.extend(_validate_config_fields(config))
    
    # Submission validation
    errors.extend(_validate_config_submissions(config))
    
    # Conference validation
    errors.extend(_validate_config_conferences(config))
    
    # Constants validation
    try:
        from src.validation.constants import validate_constants
        constants_errors = validate_constants()
        if constants_errors:
            errors.extend([f"Constants validation: {error}" for error in constants_errors])
    except ImportError:
        # Constants validation not available, skip
        pass
    
    return errors



def _validate_config_fields(config: Config) -> List[str]:
    """Validate configuration field values and return list of errors."""
    errors = []
    
    # Validate basic requirements
    if not config.submissions:
        errors.append("No submissions defined")
    if not config.conferences:
        errors.append("No conferences defined")
    if config.min_abstract_lead_time_days < 0:
        errors.append("Min abstract lead time cannot be negative")
    if config.min_paper_lead_time_days < 0:
        errors.append("Min paper lead time cannot be negative")
    if config.max_concurrent_submissions < 1:
        errors.append("Max concurrent submissions must be at least 1")
    
    return errors


def _validate_config_submissions(config: Config) -> List[str]:
    """Validate submission-related configuration and return list of errors."""
    errors = []
    
    # Validate submissions - first pass: build submission IDs and validate basic submission data
    submission_ids = set()
    # Validate each submission individually
    for submission in config.submissions:
        from src.validation.submission import validate_submission_constraints
        from src.core.models import Schedule
        from datetime import date
        empty_schedule = Schedule()
        submission_errors = validate_submission_constraints(submission, date.today(), empty_schedule, config)
        errors.extend([f"Submission {submission.id}: {error}" for error in submission_errors])
        if submission.id in submission_ids:
            errors.append(f"Duplicate submission ID: {submission.id}")
        submission_ids.add(submission.id)
    
    # Second pass: validate cross-references (conferences and dependencies)
    for submission in config.submissions:
        # Validate conference reference
        if submission.conference_id:
            conference_ids = {conf.id for conf in config.conferences}
            if submission.conference_id not in conference_ids:
                errors.append(f"Submission {submission.id} references unknown conference {submission.conference_id}")
        
        # Validate dependencies
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id not in submission_ids:
                    errors.append(f"Submission {submission.id} depends on nonexistent submission {dep_id}")
    
    return errors


def _validate_config_conferences(config: Config) -> List[str]:
    """Validate conference-related configuration and return list of errors."""
    errors = []
    
    # Validate conferences
    conference_ids = set()
    for conference in config.conferences:
        # Basic field validation
        if not conference.id:
            errors.append("Conference missing ID")
        if not conference.name:
            errors.append("Conference missing name")
        if not conference.deadlines:
            errors.append(f"Conference {conference.id}: No deadlines defined")
        for submission_type, deadline in conference.deadlines.items():
            if not isinstance(deadline, date):
                errors.append(f"Conference {conference.id}: Invalid deadline format for {submission_type}")
        
        if conference.id in conference_ids:
            errors.append(f"Duplicate conference ID: {conference.id}")
        conference_ids.add(conference.id)
    
    return errors
