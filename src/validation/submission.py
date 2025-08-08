"""Individual submission validation functions."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission
from src.core.constants import QUALITY_CONSTANTS
from .deadline import _validate_deadline_compliance_single


def validate_submission_placement(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
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



