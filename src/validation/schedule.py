"""Schedule validation functions for complete schedule analysis."""

from typing import Dict, Any
from datetime import date, timedelta

from src.core.models import Config, Submission, SubmissionType, ConstraintValidationResult
from src.core.constants import QUALITY_CONSTANTS
from src.validation.deadline import validate_deadline_constraints
from src.validation.resources import validate_resources_constraints
from src.validation.venue import validate_venue_constraints


def validate_schedule_constraints(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate all constraints on the complete schedule and return detailed results."""
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
    
    # Use the structured validation function
    structured_result = _validate_schedule_constraints_structured(schedule, config)
    
    # Get additional analytics
    from src.analytics.schedule_analysis import analyze_schedule_with_scoring
    analytics = analyze_schedule_with_scoring(schedule, config)
    
    # Get additional validation results that penalty functions expect
    from .deadline import _validate_blackout_dates, _validate_paper_lead_time_months
    from .venue import _validate_conference_compatibility, _validate_single_conference_policy
    
    blackout_result = _validate_blackout_dates(schedule, config)
    lead_time_result = _validate_paper_lead_time_months(schedule, config)
    conference_compatibility_result = _validate_conference_compatibility(schedule, config)
    single_conference_result = _validate_single_conference_policy(schedule, config)
    
    # Create soft block model validation (simplified)
    soft_block_result = _validate_soft_block_model(schedule, config)
    
    # Create abstract-paper dependency validation
    abstract_paper_result = _validate_abstract_paper_dependencies(schedule, config)
    
    # Combine results
    all_violations = (
        structured_result.deadlines.violations +
        structured_result.dependencies.violations +
        structured_result.resources.violations +
        blackout_result.get("violations", []) +
        lead_time_result.get("violations", []) +
        conference_compatibility_result.get("violations", []) +
        single_conference_result.get("violations", []) +
        soft_block_result.get("violations", []) +
        abstract_paper_result.get("violations", [])
    )
    
    # Determine overall validity
    is_valid = len(all_violations) == 0
    
    # Calculate overall compliance rate
    total_checks = (
        structured_result.deadlines.total_submissions +
        structured_result.dependencies.total_dependencies +
        structured_result.resources.total_days +
        blackout_result.get("total_submissions", 0) +
        lead_time_result.get("total_papers", 0) +
        conference_compatibility_result.get("total_submissions", 0) +
        single_conference_result.get("total_submissions", 0) +
        soft_block_result.get("total_submissions", 0) +
        abstract_paper_result.get("total_dependencies", 0)
    )
    
    compliant_checks = (
        structured_result.deadlines.compliant_submissions +
        structured_result.dependencies.satisfied_dependencies +
        structured_result.resources.total_days - len([v for v in structured_result.resources.violations]) +
        blackout_result.get("compliant_submissions", 0) +
        lead_time_result.get("compliant_papers", 0) +
        conference_compatibility_result.get("compliant_submissions", 0) +
        single_conference_result.get("compliant_submissions", 0) +
        soft_block_result.get("compliant_submissions", 0) +
        abstract_paper_result.get("satisfied_dependencies", 0)
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
                "is_valid": structured_result.deadlines.is_valid,
                "violations": structured_result.deadlines.violations,
                "compliance_rate": structured_result.deadlines.compliance_rate
            },
            "dependencies": {
                "is_valid": structured_result.dependencies.is_valid,
                "violations": structured_result.dependencies.violations,
                "satisfaction_rate": structured_result.dependencies.satisfaction_rate
            },
            "resources": {
                "is_valid": structured_result.resources.is_valid,
                "violations": structured_result.resources.violations,
                "max_observed": structured_result.resources.max_observed
            },
            "blackout_dates": blackout_result,
            "paper_lead_time": lead_time_result,
            "conference_compatibility": conference_compatibility_result,
            "single_conference_policy": single_conference_result,
            "soft_block_model": soft_block_result,
            "abstract_paper_dependencies": abstract_paper_result
        },
        "analytics": analytics.get("schedule_analysis", {})
    }


def validate_schedule(schedule: Dict[str, date], config: Config) -> bool:
    """
    Simple boolean validation of a schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        The schedule to validate
    config : Config
        The configuration to use for validation
        
    Returns
    -------
    bool
        True if schedule is valid, False otherwise
    """
    validation_result = validate_schedule_constraints(schedule, config)
    return validation_result["summary"]["overall_valid"]


def _validate_dependency_satisfaction(schedule: Dict[str, date], config: Config):
    """Validate that all dependencies are satisfied for entire schedule."""
    from src.core.models import DependencyValidation, DependencyViolation
    
    perfect_satisfaction_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DependencyValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            satisfaction_rate=perfect_satisfaction_rate,
            total_dependencies=0,
            satisfied_dependencies=0
        )
    
    violations = []
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.depends_on:
            continue
        
        for dep_id in sub.depends_on:
            total_dependencies += 1
            
            # Check if dependency exists in schedule
            if dep_id not in schedule:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not scheduled",
                    dependency_id=dep_id,
                    issue="missing_dependency",
                    severity="high"
                ))
                continue
            
            # Check if dependency is completed before this submission starts
            dep_start = schedule[dep_id]
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not found in submissions",
                    dependency_id=dep_id,
                    issue="invalid_dependency",
                    severity="high"
                ))
                continue
            
            dep_end = dep_sub.get_end_date(dep_start, config)
            
            if start_date < dep_end:
                days_violation = (dep_end - start_date).days
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Submission {sid} starts before dependency {dep_id} completes",
                    dependency_id=dep_id,
                    issue="timing_violation",
                    days_violation=days_violation,
                    severity="medium"
                ))
            else:
                satisfied_dependencies += 1
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * percentage_multiplier) if total_dependencies > 0 else perfect_satisfaction_rate
    is_valid = len(violations) == 0
    
    return DependencyValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"{satisfied_dependencies}/{total_dependencies} dependencies satisfied ({satisfaction_rate:.1f}%)",
        satisfaction_rate=satisfaction_rate,
        total_dependencies=total_dependencies,
        satisfied_dependencies=satisfied_dependencies
    )


def _validate_schedule_constraints_structured(schedule: Dict[str, date], config: Config) -> ConstraintValidationResult:
    """Validate all constraints for a complete schedule and return structured result."""
    # Basic validations
    deadline_result = validate_deadline_constraints(schedule, config)
    dependency_result = _validate_dependency_satisfaction(schedule, config)
    resource_result = validate_resources_constraints(schedule, config)
    
    # Additional validations
    venue_result = validate_venue_constraints(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations +
        dependency_result.violations +
        resource_result.violations +
        venue_result.get("violations", [])
    )
    
    # Calculate overall validity
    is_valid = len(all_violations) == 0
    
    return ConstraintValidationResult(
        deadlines=deadline_result,
        dependencies=dependency_result,
        resources=resource_result,
        is_valid=is_valid
    )


def _validate_soft_block_model(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate soft block model constraints (PCCP)."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.earliest_start_date:
            continue
        
        total_submissions += 1
        
        # Check if submission is within ±2 months (60 days) of earliest start date
        days_diff = abs((start_date - sub.earliest_start_date).days)
        
        if days_diff > 60:
            violations.append({
                "submission_id": sid,
                "description": f"Submission scheduled {days_diff} days from earliest start date (max 60 days)",
                "severity": "medium",
                "days_violation": days_diff - 60,
                "earliest_start_date": sub.earliest_start_date,
                "scheduled_date": start_date
            })
        else:
            compliant_submissions += 1
    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions within soft block constraints",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions
    }


def _validate_abstract_paper_dependencies(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate abstract-paper dependency relationships."""
    violations = []
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        # Find corresponding abstract for this paper
        paper_base_id = sid.split('-pap-')[0] if '-pap-' in sid else None
        conference_id = sid.split('-pap-')[1] if '-pap-' in sid else None
        
        if not paper_base_id or not conference_id:
            continue
        
        abstract_id = f"{paper_base_id}-abs-{conference_id}"
        
        if abstract_id in schedule:
            total_dependencies += 1
            
            # Check if abstract is completed before paper starts
            abstract_start = schedule[abstract_id]
            abstract_sub = config.submissions_dict.get(abstract_id)
            
            if abstract_sub:
                abstract_duration = abstract_sub.get_duration_days(config)
                abstract_end = abstract_start + timedelta(days=abstract_duration)
                
                if start_date < abstract_end:
                    days_violation = (abstract_end - start_date).days
                    violations.append({
                        "submission_id": sid,
                        "description": f"Paper starts before abstract completes",
                        "severity": "high",
                        "days_violation": days_violation,
                        "abstract_id": abstract_id,
                        "issue": "timing_violation"
                    })
                else:
                    satisfied_dependencies += 1
            else:
                violations.append({
                    "submission_id": sid,
                    "description": f"Abstract {abstract_id} not found in submissions",
                    "severity": "high",
                    "abstract_id": abstract_id,
                    "issue": "missing_dependency"
                })
    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"{satisfied_dependencies}/{total_dependencies} abstract-paper dependencies satisfied",
        "total_dependencies": total_dependencies,
        "satisfied_dependencies": satisfied_dependencies
    }
