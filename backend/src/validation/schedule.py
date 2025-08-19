"""Schedule validation functions for comprehensive schedule constraint validation."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Schedule, ValidationResult
from src.validation.resources import validate_resources_constraints
from src.validation.venue import validate_venue_constraints
from src.validation.deadline import validate_deadline_constraints


def validate_schedule_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate comprehensive schedule constraints including deadlines, resources, and venue."""
    if not schedule:
        return ValidationResult(
            is_valid=False, 
            violations=[], 
            summary="No schedule to validate",
            metadata={
                "total_submissions": 0,
                "compliant_submissions": 0
            }
        )
    
    # Validate all constraint types
    deadline_result = validate_deadline_constraints(schedule, config)
    resource_result = validate_resources_constraints(schedule, config)
    venue_result = validate_venue_constraints(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations + 
        resource_result.violations + 
        venue_result.violations
    )
    
    # Calculate totals
    total_submissions = len(schedule.intervals)
    compliant_submissions = sum([
        deadline_result.metadata.get("compliant_submissions", 0),
        resource_result.metadata.get("compliant_submissions", 0),
        venue_result.metadata.get("compliant_submissions", 0)
    ])
    
    # Overall validation
    is_valid = len(all_violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=all_violations,
        summary=f"Schedule validation: {len(all_violations)} violations found",
        metadata={
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
    )
