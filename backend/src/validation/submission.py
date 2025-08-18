"""Individual submission validation functions."""

from typing import Dict, Any, List
from datetime import date

from ..core.models import Config, Submission, SubmissionType, Schedule
from ..core.constants import QUALITY_CONSTANTS


def validate_submission(submission: Submission) -> List[str]:
    """Validate basic submission fields and return list of errors."""
    errors = []
    
    if not submission.id:
        errors.append("Missing submission ID")
    if not submission.title:
        errors.append("Missing title")
    
    # Papers need either conference_id or preferred_conferences
    if submission.kind == SubmissionType.PAPER and not submission.conference_id and submission.preferred_conferences is None:
        errors.append("Papers must have either conference_id or preferred_conferences")
    
    if submission.draft_window_months < 0:
        errors.append("Draft window months cannot be negative")
    if submission.lead_time_from_parents < 0:
        errors.append("Lead time from parents cannot be negative")
    if submission.penalty_cost_per_day is not None and submission.penalty_cost_per_day < 0:
        errors.append("Penalty cost per day cannot be negative")
    if submission.penalty_cost_per_month is not None and submission.penalty_cost_per_month < 0:
        errors.append("Penalty cost per month cannot be negative")
    if submission.free_slack_months is not None and submission.free_slack_months < 0:
        errors.append("Free slack months cannot be negative")
    
    return errors


def validate_submission_constraints(submission: Submission, start_date: date, schedule: Schedule, config: Config) -> bool:
    """Validate if a submission can be placed at a specific date in the schedule."""
    # Basic deadline check
    if not _validate_deadline_compliance_single(start_date, submission, config):
        return False
    
    # Basic dependency check
    if not _validate_dependencies_satisfied(submission, schedule, config, start_date):
        return False
    
    # Basic venue compatibility check
    try:
        from .venue import _validate_venue_compatibility
        _validate_venue_compatibility({submission.id: submission}, config)
    except ValueError:
        return False
    
    # Validate unified schema fields
    if not _validate_unified_schema_fields(submission):
        return False
    
    return True


def _validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """Validate deadline compliance for a single submission."""
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return True
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start_date, config)
    
    return end_date <= deadline


def _validate_dependencies_satisfied(submission: Submission, schedule: Schedule, config: Config, current_date: date) -> bool:
    """Check if all dependencies are satisfied for this submission."""
    if not submission.depends_on:
        return True
    
    for dep_id in submission.depends_on:
        if dep_id not in schedule.intervals:
            return False
        
        dep_start = schedule.intervals[dep_id].start_date
        dep_sub = config.get_submission(dep_id)
        if not dep_sub:
            return False
        
        dep_end = dep_sub.get_end_date(dep_start, config)
        if current_date < dep_end:
            return False
    
    return True


def _validate_venue_compatibility(submission: Submission, config: Config) -> None:
    """Validate venue compatibility for a submission."""
    if not submission.conference_id:
        return
    
    if not config.has_conference(submission.conference_id):
        return
    
    conf = config.get_conference(submission.conference_id)


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



