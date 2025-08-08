"""Schedule validation functions for complete schedule analysis."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission, ConstraintValidationResult
from src.core.constants import QUALITY_CONSTANTS

from .deadline import validate_deadline_compliance
from .constraints import validate_dependency_satisfaction
from .resources import validate_resource_constraints
from .venue import validate_conference_compatibility, validate_conference_submission_compatibility, validate_single_conference_policy


def validate_all_constraints(schedule: Dict[str, date], config: Config) -> ConstraintValidationResult:
    """Validate all constraints and return basic structured result."""
    # Basic validations
    deadline_result = validate_deadline_compliance(schedule, config)
    dependency_result = validate_dependency_satisfaction(schedule, config)
    resource_result = validate_resource_constraints(schedule, config)
    
    # Additional validations
    blackout_result = validate_blackout_dates(schedule, config)
    conference_compat_result = validate_conference_compatibility(schedule, config)
    conf_sub_compat_result = validate_conference_submission_compatibility(schedule, config)
    single_conf_result = validate_single_conference_policy(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations +
        dependency_result.violations +
        resource_result.violations +
        blackout_result.get("violations", []) +
        conference_compat_result.get("violations", []) +
        conf_sub_compat_result.get("violations", []) +
        single_conf_result.get("violations", [])
    )
    
    # Calculate overall validity
    is_valid = len(all_violations) == 0
    
    return ConstraintValidationResult(
        deadlines=deadline_result,
        dependencies=dependency_result,
        resources=resource_result,
        is_valid=is_valid
    )


def validate_all_constraints_comprehensive(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate all constraints comprehensively and return detailed results."""
    if not schedule:
        return {
            "summary": {
                "overall_valid": True,
                "total_violations": 0,
                "compliance_rate": QUALITY_CONSTANTS.perfect_compliance_rate
            },
            "constraints": {},
            "analytics": {}
        }
    
    # Run all validations
    deadline_result = validate_deadline_compliance(schedule, config)
    dependency_result = validate_dependency_satisfaction(schedule, config)
    resource_result = validate_resource_constraints(schedule, config)
    blackout_result = validate_blackout_dates(schedule, config)
    conference_compat_result = validate_conference_compatibility(schedule, config)
    conf_sub_compat_result = validate_conference_submission_compatibility(schedule, config)
    single_conf_result = validate_single_conference_policy(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations +
        dependency_result.violations +
        resource_result.violations +
        blackout_result.get("violations", []) +
        conference_compat_result.get("violations", []) +
        conf_sub_compat_result.get("violations", []) +
        single_conf_result.get("violations", [])
    )
    
    # Determine overall validity
    is_valid = len(all_violations) == 0
    
    # Calculate overall compliance rate
    total_checks = (
        deadline_result.total_submissions +
        dependency_result.total_dependencies +
        resource_result.total_days +
        blackout_result.get("total_submissions", 0) +
        conference_compat_result.get("total_submissions", 0) +
        conf_sub_compat_result.get("total_submissions", 0) +
        single_conf_result.get("total_papers", 0)
    )
    
    compliant_checks = (
        deadline_result.compliant_submissions +
        dependency_result.satisfied_dependencies +
        resource_result.total_days - len([v for v in resource_result.violations]) +
        blackout_result.get("compliant_submissions", 0) +
        conference_compat_result.get("compatible_submissions", 0) +
        conf_sub_compat_result.get("compatible_submissions", 0) +
        single_conf_result.get("compliant_papers", 0)
    )
    
    overall_compliance_rate = (compliant_checks / total_checks * QUALITY_CONSTANTS.percentage_multiplier) if total_checks > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return {
        "summary": {
            "overall_valid": is_valid,
            "total_violations": len(all_violations),
            "compliance_rate": overall_compliance_rate
        },
        "constraints": {
            "deadlines": {
                "is_valid": deadline_result.is_valid,
                "violations": deadline_result.violations,
                "compliance_rate": deadline_result.compliance_rate
            },
            "dependencies": {
                "is_valid": dependency_result.is_valid,
                "violations": dependency_result.violations,
                "satisfaction_rate": dependency_result.satisfaction_rate
            },
            "resources": {
                "is_valid": resource_result.is_valid,
                "violations": resource_result.violations,
                "max_observed": resource_result.max_observed
            },
            "blackout_dates": blackout_result,
            "conference_compatibility": conference_compat_result,
            "conference_submission_compatibility": conf_sub_compat_result,
            "single_conference_policy": single_conf_result
        },
        "analytics": {
            "total_submissions": len(schedule),
            "total_violations": len(all_violations),
            "compliance_rate": overall_compliance_rate
        }
    }


def validate_schedule_comprehensive(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate complete schedule comprehensively."""
    # Get comprehensive validation results
    result = validate_all_constraints_comprehensive(schedule, config)
    
    # Add additional schedule analysis
    result["schedule_analysis"] = {
        "total_submissions": len(schedule),
        "schedule_span": _calculate_schedule_span(schedule) if schedule else 0,
        "average_daily_load": _calculate_average_daily_load(schedule, config) if schedule else 0
    }
    
    return result


def validate_submission_placement(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """Validate placement of a single submission (lighter version for schedulers)."""
    from .deadline import validate_deadline_compliance_single
    from .constraints import validate_dependencies_satisfied
    from .venue import validate_venue_compatibility
    
    # Basic deadline check
    if not validate_deadline_compliance_single(start_date, submission, config):
        return False
    
    # Basic dependency check
    if not validate_dependencies_satisfied(submission, schedule, config.submissions_dict, config, start_date):
        return False
    
    # Basic venue compatibility check
    try:
        validate_venue_compatibility({submission.id: submission}, config.conferences_dict)
    except ValueError:
        return False
    
    return True


def validate_submission_comprehensive(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """Validate placement of a single submission comprehensively."""
    # Create a temporary schedule with this submission
    temp_schedule = schedule.copy()
    temp_schedule[submission.id] = start_date
    
    # Run comprehensive validation on the temporary schedule
    result = validate_all_constraints_comprehensive(temp_schedule, config)
    
    return result["summary"]["overall_valid"]


def _calculate_schedule_span(schedule: Dict[str, date]) -> int:
    """Calculate the span of the schedule in days."""
    if not schedule:
        return 0
    
    start_dates = list(schedule.values())
    return (max(start_dates) - min(start_dates)).days


def _calculate_average_daily_load(schedule: Dict[str, date], config: Config) -> float:
    """Calculate average daily load."""
    if not schedule:
        return 0.0
    
    from .resources import _calculate_daily_load
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return 0.0
    
    total_load = sum(daily_load.values())
    return total_load / len(daily_load)


def validate_blackout_dates(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that no submissions are scheduled on blackout dates."""
    from .deadline import validate_blackout_dates as _validate_blackout_dates
    return _validate_blackout_dates(schedule, config)
