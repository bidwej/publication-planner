"""Blackout date validation functions for submission scheduling constraints."""

from typing import List
from datetime import date, timedelta

from ..core.models import Config, Schedule, ValidationResult, ConstraintViolation
from ..core.constants import QUALITY_CONSTANTS


def validate_blackout_dates(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate blackout date constraints."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    # Check if blackout dates are configured
    if not config.blackout_dates:
        return ValidationResult(
            is_valid=True, 
            violations=[],
            summary="No blackout dates configured",
            metadata={
                "total_submissions": 0, 
                "compliant_submissions": 0
            }
        )
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        submission_duration = sub.get_duration_days(config)
        
        for i in range(submission_duration):
            check_date = interval.start_date + timedelta(days=i)
            if check_date in config.blackout_dates:
                violations.append(ConstraintViolation(
                    submission_id=sid, 
                    description=f"Submission scheduled during blackout date {check_date}",
                    severity="high"
                ))
                break
        else:
            compliant_submissions += 1
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions avoid blackout dates",
        metadata={
            "total_submissions": total_submissions, 
            "compliant_submissions": compliant_submissions
        }
    )
