"""Individual submission validation functions."""

from typing import Dict, Any
from datetime import date

from core.models import Config, Submission
from core.constants import QUALITY_CONSTANTS
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
    
    # Validate unified schema fields
    if not _validate_unified_schema_fields(submission):
        return False
    
    return True


def _validate_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                                  submissions_dict: Dict[str, Submission], config: Config, 
                                  current_date: date) -> bool:
    """Check if all dependencies are satisfied for one submission."""
    # Use the shared dependency checking logic from models.py
    return sub.are_dependencies_satisfied(schedule, submissions_dict, config, current_date)


def _validate_unified_schema_fields(submission: Submission) -> bool:
    """Validate the unified schema fields that are common to both mods and papers."""
    
    # Validate engineering_ready_date if present
    if submission.engineering_ready_date is not None:
        if not isinstance(submission.engineering_ready_date, date):
            return False
        
        # Engineering ready date should not be in the past for active submissions
        if submission.engineering_ready_date < date.today():
            # This could be a warning rather than an error, depending on business logic
            pass
    
    # Validate free_slack_months if present
    if submission.free_slack_months is not None:
        if not isinstance(submission.free_slack_months, int):
            return False
        
        if submission.free_slack_months < 0:
            return False
    
    # Validate penalty_cost_per_month if present
    if submission.penalty_cost_per_month is not None:
        if not isinstance(submission.penalty_cost_per_month, (int, float)):
            return False
        
        if submission.penalty_cost_per_month < 0:
            return False
    
    return True


def validate_submission_data_quality(submission: Submission) -> Dict[str, Any]:
    """Validate submission data quality and return quality metrics."""
    quality_metrics = {
        "has_engineering_ready_date": submission.engineering_ready_date is not None,
        "has_free_slack": submission.free_slack_months is not None,
        "has_penalty_cost": submission.penalty_cost_per_month is not None,
        "has_preferred_conferences": bool(submission.preferred_conferences),
        "has_submission_workflow": submission.submission_workflow is not None,
        "total_quality_score": 0.0
    }
    
    # Calculate quality score based on completeness
    quality_score = 0.0
    max_score = 6.0  # 6 quality indicators
    
    if quality_metrics["has_engineering_ready_date"]:
        quality_score += 1.0
    if quality_metrics["has_free_slack"]:
        quality_score += 1.0
    if quality_metrics["has_penalty_cost"]:
        quality_score += 1.0
            if quality_metrics["has_preferred_conferences"]:
        quality_score += 1.0
    if quality_metrics["has_submission_workflow"]:
        quality_score += 1.0
    
    # Bonus for having all fields
    if quality_score == max_score:
        quality_score += 0.5
    
    quality_metrics["total_quality_score"] = quality_score / max_score
    
    return quality_metrics



