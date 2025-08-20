"""Scheduler validation functions for strategy and constraint compliance."""

from typing import Dict, Any, List, Tuple
from datetime import date, timedelta

from core.models import Config, Submission, Schedule, SubmissionType, ValidationResult, ConstraintViolation
from core.constants import SCHEDULING_CONSTANTS
from validation.submission import validate_submission_constraints
from validation.dependencies import validate_dependency_constraints


def validate_scheduler_constraints(submission: Submission, start_date: date, 
                                    schedule: Schedule, config: Config) -> ValidationResult:
    """Validate all scheduler constraints for a submission at a given start date."""
    errors = []
    
    # Validate basic submission constraints
    if not _validate_scheduler_constraints(submission, start_date, schedule, config):
        errors.append(ConstraintViolation(
            submission_id=submission.id,
            description="Basic submission constraints not met",
            severity="high"
        ))
    
    # Validate concurrency constraints
    concurrency_errors = _validate_concurrency_constraints(schedule, config, start_date)
    errors.extend(concurrency_errors)
    
    # Validate working day constraints
    working_day_errors = _validate_working_day_constraints(schedule, config)
    errors.extend(working_day_errors)
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        violations=errors,
        summary=f"Scheduler validation: {len(errors)} errors found",
        metadata={
            "total_errors": len(errors)
        }
    )


def _validate_scheduler_constraints(submission: Submission, start_date: date, 
                                schedule: Schedule, config: Config) -> bool:
    """Validate all constraints for a submission at a given start date in scheduler context."""
    # Use the centralized submission validation directly with the Schedule object
    errors = validate_submission_constraints(submission, start_date, schedule, config)
    return len(errors) == 0


def validate_scheduling_window(config: Config) -> Tuple[date, date]:
    """Get the scheduling window (start and end dates) for schedulers."""
    # Use config scheduling start date if available, otherwise calculate a reasonable start date
    if hasattr(config, 'scheduling_start_date') and config.scheduling_start_date:
        start_date = config.scheduling_start_date
    else:
        # Use a reasonable reference date instead of date.today() to avoid future failures
        # This allows for historical data and resubmissions
        start_date = date.today() - timedelta(days=SCHEDULING_CONSTANTS.reference_period_days)  # 1 year ago
    
    # Find latest deadline among all conferences
    latest_deadline = start_date
    for conference in config.conferences:
        for deadline in conference.deadlines.values():
            if deadline > latest_deadline:
                latest_deadline = deadline
    
    # Add buffer for conference response time using constants
    response_buffer = SCHEDULING_CONSTANTS.conference_response_time_days
    end_date = latest_deadline + timedelta(days=response_buffer)
    
    print(f"Debug: validate_scheduling_window: start_date={start_date}, end_date={end_date}")
    print(f"Debug: Today's date: {date.today()}")
    print(f"Debug: Latest deadline: {latest_deadline}")
    print(f"Debug: Response buffer: {response_buffer}")
    
    return start_date, end_date


def _validate_concurrency_constraints(schedule: Schedule, config: Config, 
                                   current_date: date) -> List[ConstraintViolation]:
    """Validate that concurrency limits are not exceeded."""
    errors = []
    max_concurrent = config.max_concurrent_submissions
    
    # Count active submissions on current date
    active_count = 0
    for submission_id, interval in schedule.intervals.items():
        if interval.start_date <= current_date <= interval.end_date:
            active_count += 1
    
    if active_count > max_concurrent:
        errors.append(ConstraintViolation(
            submission_id="",  # General constraint violation
            description=f"Concurrency limit exceeded: {active_count} active submissions, max allowed: {max_concurrent}",
            severity="high"
        ))
    
    return errors


def _validate_working_day_constraints(schedule: Schedule, config: Config) -> List[ConstraintViolation]:
    """Validate that submissions are scheduled on working days."""
    errors = []
    
    if not config.blackout_dates:
        return errors  # No blackout dates configured
    
    for submission_id, interval in schedule.intervals.items():
        current_date = interval.start_date
        while current_date <= interval.end_date:
            if current_date in config.blackout_dates:
                errors.append(ConstraintViolation(
                    submission_id=submission_id,
                    description=f"Submission {submission_id} scheduled on blackout date: {current_date}",
                    severity="high"
                ))
            current_date += timedelta(days=1)
    
    return errors
