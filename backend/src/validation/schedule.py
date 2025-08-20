"""Schedule validation functions for comprehensive schedule constraint validation."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Schedule, ValidationResult
from src.validation.resources import validate_resources_constraints
from src.validation.venue import validate_venue_constraints
from src.validation.deadline import validate_deadline_constraints
from src.validation.dependencies import validate_dependency_constraints


def validate_schedule_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate comprehensive schedule constraints including deadlines, dependencies, resources, and venue."""
    if not schedule:
        return ValidationResult(
            is_valid=False, 
            violations=[], 
            summary="No schedule to validate",
            metadata={
                "total_submissions": 0,
                "compliant_submissions": 0,
                "total_dependencies": 0,
                "satisfied_dependencies": 0
            }
        )
    
    # Validate all constraint types
    deadline_result = validate_deadline_constraints(schedule, config)
    dependency_result = validate_dependency_constraints(schedule, config)
    resource_result = validate_resources_constraints(schedule, config)
    venue_result = validate_venue_constraints(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations + 
        dependency_result.violations +
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
    
    # Get dependency metrics
    total_dependencies = dependency_result.metadata.get("total_dependencies", 0)
    satisfied_dependencies = dependency_result.metadata.get("satisfied_dependencies", 0)
    
    # Get resource metrics
    max_observed = resource_result.metadata.get("max_observed", 0)
    total_days = resource_result.metadata.get("total_days", 0)
    
    # Overall validation
    is_valid = len(all_violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=all_violations,
        summary=f"Schedule validation: {len(all_violations)} violations found",
        metadata={
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions,
            "total_dependencies": total_dependencies,
            "satisfied_dependencies": satisfied_dependencies,
            "max_observed": max_observed,
            "total_days": total_days
        }
    )
