"""Individual submission validation functions."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission
from src.core.constants import QUALITY_CONSTANTS
from .deadline import _validate_deadline_compliance_single


def validate_submission_constraints(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """Validate if a submission can be placed at a specific date in the schedule."""
    # Basic deadline check
    if not _validate_deadline_compliance_single(start_date, submission, config):
        return False
    
    # Basic dependency check
    if not _validate_dependencies_satisfied(submission, schedule, config.submissions_dict, config, start_date):
        return False
    
    # Basic venue compatibility check
    try:
        from .venue import _validate_venue_compatibility
        _validate_venue_compatibility({submission.id: submission}, config.conferences_dict)
    except ValueError:
        return False
    
    return True


def _validate_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                                  submissions_dict: Dict[str, Submission], config: Config, 
                                  current_date: date) -> bool:
    """Check if all dependencies are satisfied for one submission."""
    # Use the shared dependency checking logic from models.py
    return sub.are_dependencies_satisfied(schedule, submissions_dict, config, current_date)



