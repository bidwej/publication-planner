"""Individual submission validation functions."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission
from src.core.constants import QUALITY_CONSTANTS


def validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """Validate deadline compliance for a single submission."""
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return True
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start_date, config)
    
    return end_date <= deadline


def validate_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                                  submissions_dict: Dict[str, Submission], config: Config, 
                                  current_date: date) -> bool:
    """Check if all dependencies are satisfied for one submission."""
    if not sub.depends_on:
        return True
    
    for dep_id in sub.depends_on:
        # Check if dependency exists
        if dep_id not in submissions_dict:
            return False
        
        # Check if dependency is scheduled
        if dep_id not in schedule:
            return False
        
        # Check if dependency is completed
        dep = submissions_dict[dep_id]
        dep_start = schedule[dep_id]
        dep_end = dep.get_end_date(dep_start, config)
        
        if current_date < dep_end:
            return False
    
    return True


def validate_venue_compatibility(submissions: Dict[str, Submission], conferences: Dict[str, Any]) -> None:
    """Validate venue compatibility between submissions and conferences."""
    from src.core.models import SubmissionType, ConferenceType
    
    for sid, sub in submissions.items():
        if not sub.conference_id or sub.conference_id not in conferences:
            continue
        
        conf = conferences[sub.conference_id]
        
        # Check if conference accepts this submission type
        if not conf.accepts_submission_type(sub.kind):
            raise ValueError(f"Submission {sid} ({sub.kind.value}) not accepted by conference {sub.conference_id}")
        
        # Check if submission type is compatible with conference type
        if sub.kind == SubmissionType.ABSTRACT and conf.conf_type == ConferenceType.ENGINEERING:
            raise ValueError(f"Abstract {sid} not compatible with engineering conference {sub.conference_id}")


def validate_submission_placement(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """Validate if a submission can be placed at a specific date in the schedule."""
    # Basic deadline check
    if not validate_deadline_compliance_single(start_date, submission, config):
        return False
    
    # Basic dependency check
    if not validate_dependencies_satisfied(submission, schedule, config.submissions_dict, config, start_date):
        return False
    
    # Basic venue compatibility check
    try:
        validate_venue_compatibility({submission.id: submission}, config.conferences_dict)
    except ValueError:
        return False
    
    return True
