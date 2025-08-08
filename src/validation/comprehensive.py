"""Comprehensive validation functions that combine multiple validation types."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, ConstraintValidationResult, Submission
from src.core.constants import QUALITY_CONSTANTS

# Import all validation functions
from .temporal import (
    validate_deadline_compliance,
    validate_blackout_dates,
    validate_paper_lead_time_months,
    _validate_early_abstract_scheduling,
    _validate_conference_response_time,
    _validate_working_days_only
)

from .dependencies import (
    validate_dependency_satisfaction,
    validate_abstract_paper_dependencies
)

from .concurrency import (
    validate_resource_constraints
)

from .venue_rules import (
    validate_conference_compatibility,
    validate_conference_submission_compatibility,
    validate_single_conference_policy
)

from .penalties import (
    validate_priority_weighting
)

from .recurrence import (
    validate_soft_block_model
)


def validate_all_constraints(schedule: Dict[str, date], config: Config) -> ConstraintValidationResult:
    """Validate all constraints and return comprehensive result."""
    # Basic validations
    deadline_result = validate_deadline_compliance(schedule, config)
    dependency_result = validate_dependency_satisfaction(schedule, config)
    resource_result = validate_resource_constraints(schedule, config)
    
    # Additional validations
    blackout_result = validate_blackout_dates(schedule, config)
    conference_compat_result = validate_conference_compatibility(schedule, config)
    conf_sub_compat_result = validate_conference_submission_compatibility(schedule, config)
    single_conf_result = validate_single_conference_policy(schedule, config)
    soft_block_result = validate_soft_block_model(schedule, config)
    lead_time_result = validate_paper_lead_time_months(schedule, config)
    priority_result = validate_priority_weighting(schedule, config)
    abstract_paper_result = validate_abstract_paper_dependencies(schedule, config)
    
    # Timing validations
    early_abstract_violations = _validate_early_abstract_scheduling(schedule, config)
    response_time_violations = _validate_conference_response_time(schedule, config)
    working_days_violations = _validate_working_days_only(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations +
        dependency_result.violations +
        resource_result.violations +
        blackout_result.get("violations", []) +
        conference_compat_result.get("violations", []) +
        conf_sub_compat_result.get("violations", []) +
        single_conf_result.get("violations", []) +
        soft_block_result.get("violations", []) +
        lead_time_result.get("violations", []) +
        priority_result.get("violations", []) +
        abstract_paper_result.get("violations", []) +
        early_abstract_violations +
        response_time_violations +
        working_days_violations
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
    soft_block_result = validate_soft_block_model(schedule, config)
    lead_time_result = validate_paper_lead_time_months(schedule, config)
    priority_result = validate_priority_weighting(schedule, config)
    abstract_paper_result = validate_abstract_paper_dependencies(schedule, config)
    
    # Timing validations
    early_abstract_violations = _validate_early_abstract_scheduling(schedule, config)
    response_time_violations = _validate_conference_response_time(schedule, config)
    working_days_violations = _validate_working_days_only(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations +
        dependency_result.violations +
        resource_result.violations +
        blackout_result.get("violations", []) +
        conference_compat_result.get("violations", []) +
        conf_sub_compat_result.get("violations", []) +
        single_conf_result.get("violations", []) +
        soft_block_result.get("violations", []) +
        lead_time_result.get("violations", []) +
        priority_result.get("violations", []) +
        abstract_paper_result.get("violations", []) +
        early_abstract_violations +
        response_time_violations +
        working_days_violations
    )
    
    # Calculate comprehensive analytics (without scoring to avoid recursion)
    comprehensive_analytics = _calculate_comprehensive_analytics(schedule, config)
    
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
        single_conf_result.get("total_papers", 0) +
        soft_block_result.get("total_submissions", 0) +
        lead_time_result.get("total_papers", 0) +
        priority_result.get("total_submissions", 0) +
        abstract_paper_result.get("total_papers", 0)
    )
    
    total_compliant = (
        deadline_result.compliant_submissions +
        dependency_result.satisfied_dependencies +
        blackout_result.get("compliant_submissions", 0) +
        conference_compat_result.get("compatible_submissions", 0) +
        conf_sub_compat_result.get("compatible_submissions", 0) +
        single_conf_result.get("compliant_papers", 0) +
        soft_block_result.get("compliant_submissions", 0) +
        lead_time_result.get("compliant_papers", 0) +
        priority_result.get("properly_weighted", 0) +
        abstract_paper_result.get("valid_papers", 0)
    )
    
    compliance_rate = (total_compliant / total_checks * QUALITY_CONSTANTS.percentage_multiplier) if total_checks > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return {
        "summary": {
            "overall_valid": is_valid,
            "total_violations": len(all_violations),
            "compliance_rate": compliance_rate,
            "total_checks": total_checks,
            "total_compliant": total_compliant
        },
        "total_violations": len(all_violations),
        "deadlines": deadline_result,
        "dependencies": dependency_result,
        "resources": resource_result,
        "blackout_dates": blackout_result,
        "conference_compatibility": conference_compat_result,
        "conference_submission_compatibility": conf_sub_compat_result,
        "single_conference_policy": single_conf_result,
        "soft_block_model": soft_block_result,
        "paper_lead_time": lead_time_result,
        "priority_weighting": priority_result,
        "abstract_paper_dependencies": abstract_paper_result,
        "scheduling_options": {
            "early_abstract_scheduling": {
                "violations": early_abstract_violations,
                "is_valid": len(early_abstract_violations) == 0
            },
            "conference_response_time": {
                "violations": response_time_violations,
                "is_valid": len(response_time_violations) == 0
            },
            "working_days_only": {
                "violations": working_days_violations,
                "is_valid": len(working_days_violations) == 0
            }
        },
        "analytics": comprehensive_analytics
    }


def validate_schedule_comprehensive(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate schedule comprehensively and return detailed results."""
    # First run the existing comprehensive validation
    result = validate_all_constraints_comprehensive(schedule, config)
    
    # Add comprehensive single-submission validation for each submission
    comprehensive_violations = []
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if submission:
            # Use comprehensive validation for each submission
            if not validate_single_submission_constraints_comprehensive(submission, start_date, schedule, config):
                comprehensive_violations.append({
                    "submission_id": submission_id,
                    "description": f"Comprehensive validation failed for {submission_id}",
                    "severity": "high"
                })
    
    # Add comprehensive violations to the result
    if comprehensive_violations:
        if "constraints" not in result:
            result["constraints"] = {}
        if "comprehensive_violations" not in result["constraints"]:
            result["constraints"]["comprehensive_violations"] = []
        result["constraints"]["comprehensive_violations"].extend(comprehensive_violations)
        
        # Update overall validity
        result["summary"]["overall_valid"] = False
        result["summary"]["total_violations"] += len(comprehensive_violations)
    
    # Transform the result to match expected test structure
    if 'constraints' in result:
        # Convert to the format expected by tests
        transformed_result = {
            "is_valid": result["summary"]["overall_valid"],
            "violations": result["summary"]["total_violations"],
            "constraints": result["constraints"],
            "summary": result["summary"],
            "analytics": result.get("analytics", {}),
            "scores": result.get("scores", {})
        }
        return transformed_result
    
    return result


def validate_submission_placement(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """Validate placement of a single submission (lighter version for schedulers)."""
    from .temporal import validate_deadline_compliance_single
    from .dependencies import validate_dependencies_satisfied
    from .venue_rules import validate_venue_compatibility
    
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


def validate_scheduling_options(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate scheduling options and return results."""
    violations = []
    
    # Check if scheduling_options exists
    if not config.scheduling_options:
        return {
            "is_valid": True,
            "violations": [],
            "summary": "No scheduling options configured"
        }
    
    # Validate early abstract scheduling
    early_abstract_violations = _validate_early_abstract_scheduling(schedule, config)
    violations.extend(early_abstract_violations)
    
    # Validate conference response time
    response_time_violations = _validate_conference_response_time(schedule, config)
    violations.extend(response_time_violations)
    
    # Validate working days only
    working_days_violations = _validate_working_days_only(schedule, config)
    violations.extend(working_days_violations)
    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"Scheduling options: {len(violations)} violations found"
    }


def _calculate_comprehensive_scores(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Calculate comprehensive scores for the schedule."""
    if not schedule:
        return {
            "quality_score": 0.0,
            "efficiency_score": 0.0,
            "penalty_score": 0.0,
            "overall_score": 0.0
        }
    
    # Import scoring functions
    from src.scoring.quality import calculate_quality_score
    from src.scoring.efficiency import calculate_efficiency_score
    from src.scoring.penalty import calculate_penalty_score
    
    # Calculate scores
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    penalty_breakdown = calculate_penalty_score(schedule, config)
    
    # Calculate overall score (weighted average)
    overall_score = (quality_score * 0.4 + efficiency_score * 0.4 + (100 - penalty_breakdown.total_penalty) * 0.2)
    
    return {
        "quality_score": quality_score,
        "efficiency_score": efficiency_score,
        "penalty_score": penalty_breakdown.total_penalty,
        "overall_score": overall_score
    }


def _calculate_comprehensive_analytics(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Calculate comprehensive analytics for the schedule."""
    if not schedule:
        return {
            "resource_utilization": 0.0,
            "deadline_compliance": 0.0,
            "dependency_satisfaction": 0.0,
            "venue_compatibility": 0.0
        }
    
    # Calculate resource utilization
    from .concurrency import _calculate_daily_load
    daily_load = _calculate_daily_load(schedule, config)
    max_concurrent = config.max_concurrent_submissions
    
    if daily_load:
        avg_utilization = sum(daily_load.values()) / len(daily_load)
        peak_utilization = max(daily_load.values())
        resource_utilization = min(100.0, (avg_utilization / max_concurrent) * 100) if max_concurrent > 0 else 0.0
    else:
        resource_utilization = 0.0
    
    # Calculate deadline compliance
    deadline_result = validate_deadline_compliance(schedule, config)
    deadline_compliance = deadline_result.compliance_rate
    
    # Calculate dependency satisfaction
    dependency_result = validate_dependency_satisfaction(schedule, config)
    dependency_satisfaction = dependency_result.satisfaction_rate
    
    # Calculate venue compatibility
    venue_result = validate_conference_compatibility(schedule, config)
    venue_compatibility = venue_result.get("compatibility_rate", 100.0)
    
    return {
        "resource_utilization": resource_utilization,
        "deadline_compliance": deadline_compliance,
        "dependency_satisfaction": dependency_satisfaction,
        "venue_compatibility": venue_compatibility,
        "total_submissions": len(schedule),
        "schedule_duration": max(daily_load.keys()) - min(daily_load.keys()) if daily_load else 0
    }


# Legacy function names for backward compatibility
validate_single_submission_constraints = validate_submission_placement
validate_single_submission_constraints_comprehensive = validate_submission_comprehensive
