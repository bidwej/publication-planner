"""Blackout date validation functions for schedule feasibility."""

from typing import Dict, Any, List
from datetime import date, timedelta

from core.models import Config, Schedule, ValidationResult, ConstraintViolation
from core.constants import QUALITY_CONSTANTS


def validate_blackout_constraints(schedule: Schedule, config: Config) -> ValidationResult:
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
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        total_submissions += 1
        # Use the schedule's interval duration, not the submission's calculated duration
        submission_duration = interval.duration_days
        
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
    
    return _build_validation_result(
        violations,
        total_submissions,
        compliant_submissions,
        "{compliant}/{total} submissions avoid blackout dates"
    )


def _build_validation_result(violations, total_submissions, compliant_submissions, summary_template):
    """Helper to build standardized ValidationResult objects for blackout validation."""
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        summary=summary_template.format(
            compliant=compliant_submissions, 
            total=total_submissions, 
            rate=compliance_rate
        ),
        metadata={
            "compliance_rate": compliance_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
    )
