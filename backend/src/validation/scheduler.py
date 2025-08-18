"""Scheduler-specific validation functions."""

from typing import Dict, List, Tuple
from datetime import date, timedelta

from core.models import Config, Submission, Schedule, SubmissionType
from core.constants import SCHEDULING_CONSTANTS
from .submission import validate_submission_constraints
from .dependencies import validate_dependencies_satisfied


def validate_scheduler_constraints(submission: Submission, start_date: date, 
                                schedule: Schedule, config: Config) -> bool:
    """Validate all constraints for a submission at a given start date in scheduler context."""
    # Convert Schedule to Schedule for existing validation functions
    schedule_dict = {sub_id: interval.start_date for sub_id, interval in schedule.intervals.items()}
    
    # Use the centralized submission validation
    return validate_submission_constraints(submission, start_date, schedule_dict, config)


def validate_scheduling_window(config: Config) -> Tuple[date, date]:
    """Get the scheduling window (start and end dates) for schedulers."""
    # Use config start date if available, otherwise fall back to today
    start_date = getattr(config, 'start_date', None) or date.today()
    
    # Find latest deadline among all conferences
    latest_deadline = start_date
    for conference in config.conferences:
        for deadline in conference.deadlines.values():
            if deadline > latest_deadline:
                latest_deadline = deadline
    
    # Add buffer for conference response time using constants
    response_buffer = SCHEDULING_CONSTANTS.conference_response_time_days
    end_date = latest_deadline + timedelta(days=response_buffer)
    
    return start_date, end_date


def validate_concurrency_constraints(schedule: Schedule, config: Config, 
                                   current_date: date) -> List[str]:
    """Validate that concurrency limits are not exceeded."""
    errors = []
    max_concurrent = config.max_concurrent_submissions
    
    # Count active submissions on current date
    active_count = 0
    for submission_id, interval in schedule.intervals.items():
        if interval.start_date <= current_date <= interval.end_date:
            active_count += 1
    
    if active_count > max_concurrent:
        errors.append(f"Concurrency limit exceeded: {active_count} active submissions, max allowed: {max_concurrent}")
    
    return errors


def validate_working_day_constraints(schedule: Schedule, config: Config) -> List[str]:
    """Validate that submissions are scheduled on working days."""
    errors = []
    
    if not config.blackout_dates:
        return errors  # No blackout dates configured
    
    for submission_id, interval in schedule.intervals.items():
        current_date = interval.start_date
        while current_date <= interval.end_date:
            if current_date in config.blackout_dates:
                errors.append(f"Submission {submission_id} scheduled on blackout date: {current_date}")
            current_date += timedelta(days=1)
    
    return errors


def validate_earliest_start_constraints(schedule: Schedule, config: Config) -> List[str]:
    """Validate that submissions respect their earliest start date constraints."""
    errors = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.submissions_dict.get(submission_id)
        if submission and submission.earliest_start_date:
            if interval.start_date < submission.earliest_start_date:
                errors.append(f"Submission {submission_id} scheduled before earliest start date: "
                           f"scheduled {interval.start_date}, earliest allowed {submission.earliest_start_date}")
    
    return errors


def validate_engineering_ready_constraints(schedule: Schedule, config: Config) -> List[str]:
    """Validate that engineering submissions respect engineering ready dates."""
    errors = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.submissions_dict.get(submission_id)
        if submission and submission.engineering and submission.engineering_ready_date:
            if interval.start_date < submission.engineering_ready_date:
                errors.append(f"Engineering submission {submission_id} scheduled before engineering ready date: "
                           f"scheduled {interval.start_date}, engineering ready {submission.engineering_ready_date}")
    
    return errors
