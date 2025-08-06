"""Constraint validation for schedules."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date, timedelta
from .models import Config, Submission, SubmissionType, DeadlineValidation, DependencyValidation, ResourceValidation, DeadlineViolation, DependencyViolation, ResourceViolation, ConstraintValidationResult


def validate_deadline_compliance(schedule: Dict[str, date], config: Config) -> DeadlineValidation:
    """Validate that all submissions meet their deadlines."""
    if not schedule:
        return DeadlineValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            compliance_rate=100.0,
            total_submissions=0,
            compliant_submissions=0
        )
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Skip submissions without deadlines
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        total_submissions += 1
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date using proper duration logic
        end_date = sub.get_end_date(start_date, config)
        
        # Check if deadline is met
        if end_date <= deadline:
            compliant_submissions += 1
        else:
            days_late = (end_date - deadline).days
            violations.append(DeadlineViolation(
                submission_id=sid,
                description=f"Deadline missed by {days_late} days",
                severity="high" if days_late > 7 else "medium" if days_late > 1 else "low",
                submission_title=sub.title,
                conference_id=sub.conference_id,
                submission_type=sub.kind.value,
                deadline=deadline,
                end_date=end_date,
                days_late=days_late
            ))
    
    compliance_rate = (compliant_submissions / total_submissions * 100) if total_submissions > 0 else 100.0
    is_valid = len(violations) == 0
    
    return DeadlineValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions meet deadlines ({compliance_rate:.1f}%)",
        compliance_rate=compliance_rate,
        total_submissions=total_submissions,
        compliant_submissions=compliant_submissions
    )

def validate_dependency_satisfaction(schedule: Dict[str, date], config: Config) -> DependencyValidation:
    """Validate that all dependencies are satisfied."""
    if not schedule:
        return DependencyValidation(
            is_valid=True,
            violations=[],
            summary="No dependencies to validate",
            satisfaction_rate=100.0,
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
                    description=f"Dependency {dep_id} is not scheduled",
                    severity="high",
                    dependency_id=dep_id,
                    issue="missing_dependency"
                ))
                continue
            
            # Check if dependency is satisfied
            dep_start = schedule[dep_id]
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not found in config",
                    severity="high",
                    dependency_id=dep_id,
                    issue="invalid_dependency"
                ))
                continue
            
            # Calculate dependency end date using proper duration logic
            dep_end = _get_submission_end_date(dep_start, dep_sub, config)
            
            # Check if dependency is completed before this submission starts
            if dep_end > start_date:
                days_violation = (dep_end - start_date).days
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} ends {days_violation} days after submission {sid} starts",
                    severity="medium",
                    dependency_id=dep_id,
                    issue="timing_violation",
                    days_violation=days_violation
                ))
            else:
                satisfied_dependencies += 1
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * 100) if total_dependencies > 0 else 100.0
    is_valid = len(violations) == 0
    
    return DependencyValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"{satisfied_dependencies}/{total_dependencies} dependencies satisfied ({satisfaction_rate:.1f}%)",
        satisfaction_rate=satisfaction_rate,
        total_dependencies=total_dependencies,
        satisfied_dependencies=satisfied_dependencies
    )

def validate_resource_constraints(schedule: Dict[str, date], config: Config) -> ResourceValidation:
    """Validate that resource constraints (concurrency limits) are respected."""
    if not schedule:
        return ResourceValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            max_concurrent=0,
            max_observed=0,
            total_days=0
        )
    
    violations = []
    daily_load = {}
    max_concurrent = config.max_concurrent_submissions
    
    # Calculate daily workload
    daily_load = _calculate_daily_load(schedule, config)
    
    # Check for violations
    max_observed = 0
    for day, load in daily_load.items():
        max_observed = max(max_observed, load)
        if load > max_concurrent:
            violations.append(ResourceViolation(
                submission_id="",  # Not specific to one submission
                description=f"Day {day} has {load} active submissions (limit: {max_concurrent})",
                severity="medium",
                date=day,
                load=load,
                limit=max_concurrent,
                excess=load - max_concurrent
            ))
    
    is_valid = len(violations) == 0
    
    return ResourceValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"Max concurrent: {max_observed}/{max_concurrent} ({len(violations)} violations)",
        max_concurrent=max_concurrent,
        max_observed=max_observed,
        total_days=len(daily_load)
    )

def validate_all_constraints(schedule: Dict[str, date], config: Config) -> ConstraintValidationResult:
    """Validate all constraints for a schedule."""
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    return ConstraintValidationResult(
        deadlines=deadline_validation,
        dependencies=dependency_validation,
        resources=resource_validation,
        is_valid=(deadline_validation.is_valid and 
                  dependency_validation.is_valid and 
                  resource_validation.is_valid)
    )


def _get_submission_duration_days(sub: Submission, config: Config) -> int:
    """
    Calculate the duration in days for a submission.
    
    This is the centralized logic for duration calculation used across
    the entire codebase to ensure consistency.
    
    Parameters
    ----------
    sub : Submission
        The submission to calculate duration for
    config : Config
        Configuration containing default durations
        
    Returns
    -------
    int
        Duration in days
    """
    if sub.kind == SubmissionType.ABSTRACT:
        return 0  # Abstracts are instantaneous
    elif sub.kind == SubmissionType.POSTER:
        # Posters typically have shorter duration than papers
        if sub.draft_window_months > 0:
            return sub.draft_window_months * 30
        else:
            return 30  # Default 1 month for posters
    else:  # SubmissionType.PAPER
        # Use draft_window_months if available, otherwise fall back to config
        if sub.draft_window_months > 0:
            return sub.draft_window_months * 30
        else:
            return config.min_paper_lead_time_days


def _get_submission_end_date(start_date: date, sub: Submission, config: Config) -> date:
    """
    Calculate the end date for a submission.
    
    Parameters
    ----------
    start_date : date
        Start date of the submission
    sub : Submission
        The submission
    config : Config
        Configuration containing default durations
        
    Returns
    -------
    date
        End date of the submission
    """
    duration_days = _get_submission_duration_days(sub, config)
    return start_date + timedelta(days=duration_days)


def _calculate_daily_load(schedule: Dict[str, date], config: Config) -> Dict[date, int]:
    """
    Calculate daily workload from a schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Schedule mapping submission_id to start_date
    config : Config
        Configuration containing submission data
        
    Returns
    -------
    Dict[date, int]
        Mapping of date to number of active submissions
    """
    daily_load = {}
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        duration_days = _get_submission_duration_days(sub, config)
        
        # Add load for each day the submission is active
        for i in range(duration_days + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    return daily_load


def check_deadline_compliance(start_date: date, sub: Submission, config: Config) -> bool:
    """
    Check if a submission starting on the given date meets its deadline.
    
    Parameters
    ----------
    start_date : date
        Proposed start date
    sub : Submission
        The submission to check
    config : Config
        Configuration containing conference data
        
    Returns
    -------
    bool
        True if deadline is met, False otherwise
    """
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return True  # No deadline to check
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True  # No deadline for this submission type
    
    deadline = conf.deadlines[sub.kind]
    if deadline is None:
        return True  # No deadline set
    
    end_date = _get_submission_end_date(start_date, sub, config)
    return end_date <= deadline


def check_deadline_with_lookahead(sub: Submission, start: date, config: Config, 
                                 conferences: Dict[str, any], lookahead_days: int = 0) -> bool:
    """Check if starting on this date meets the deadline with optional lookahead buffer."""
    # Use the unified deadline checking logic
    base_compliance = check_deadline_compliance(start, sub, config)
    
    if not base_compliance:
        return False
    
    # Add lookahead buffer if enabled
    if lookahead_days > 0:
        if not sub.conference_id or sub.conference_id not in conferences:
            return True
        
        conf = conferences[sub.conference_id]
        if sub.kind not in conf.deadlines:
            return True
        
        deadline = conf.deadlines[sub.kind]
        if deadline is None:
            return True
        
        end_date = sub.get_end_date(start, config)
        buffer_date = deadline - timedelta(days=lookahead_days)
        return end_date <= buffer_date
    
    return True


def check_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                               submissions: Dict[str, Submission], config: Config, current: date) -> bool:
    """Check if all dependencies are satisfied."""
    if not sub.depends_on:
        return True
    for dep_id in sub.depends_on:
        if dep_id not in schedule:
            return False
        dep_end = submissions[dep_id].get_end_date(schedule[dep_id], config)
        if current < dep_end + timedelta(days=sub.lead_time_from_parents):
            return False
    return True


def validate_venue_compatibility(submissions: Dict[str, Submission], conferences: Dict[str, any]) -> None:
    """Validate that submissions are compatible with their venues."""
    for sid, submission in submissions.items():
        if submission.conference_id and submission.conference_id not in conferences:
            raise ValueError(f"Submission {sid} references unknown conference {submission.conference_id}")


def validate_schedule_comprehensive(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """
    Comprehensive schedule validation using all constraint and scoring functions.
    
    This is the main entry point for schedule validation that ensures
    all components use the same logic consistently.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Schedule to validate
    config : Config
        Configuration containing all data
        
    Returns
    -------
    Dict[str, Any]
        Comprehensive validation results including constraints, scoring, and analytics
    """
    # Import here to avoid circular imports
    from ..scoring.penalty import calculate_penalty_score
    from ..scoring.quality import calculate_quality_score
    from ..scoring.efficiency import calculate_efficiency_score
    from ..output.analytics import (
        analyze_schedule_completeness,
        analyze_schedule_distribution,
        analyze_submission_types,
        analyze_timeline,
        analyze_resources
    )
    
    # 1. Constraint validation
    constraint_result = validate_all_constraints(schedule, config)
    
    # 2. Scoring calculations
    penalty_breakdown = calculate_penalty_score(schedule, config)
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    
    # 3. Analytics
    completeness = analyze_schedule_completeness(schedule, config)
    distribution = analyze_schedule_distribution(schedule, config)
    types_analysis = analyze_submission_types(schedule, config)
    timeline = analyze_timeline(schedule, config)
    resources = analyze_resources(schedule, config)
    
    return {
        # Constraints
        "constraints": constraint_result,
        "deadline_compliance": constraint_result.deadlines.compliance_rate,
        "dependency_satisfaction": constraint_result.dependencies.satisfaction_rate,
        "resource_valid": constraint_result.resources.is_valid,
        "overall_valid": constraint_result.is_valid,
        
        # Scoring
        "penalty": penalty_breakdown,
        "quality_score": quality_score,
        "efficiency_score": efficiency_score,
        "total_penalty": penalty_breakdown.total_penalty,
        
        # Analytics
        "completeness": completeness,
        "distribution": distribution,
        "types": types_analysis,
        "timeline": timeline,
        "resources": resources,
        "completion_rate": completeness.completion_rate,
        "duration_days": timeline.duration_days,
        "peak_load": resources.peak_load,
        
        # Summary
        "summary": {
            "is_feasible": constraint_result.is_valid,
            "total_violations": (
                len(constraint_result.deadlines.violations) +
                len(constraint_result.dependencies.violations) +
                len(constraint_result.resources.violations)
            ),
            "overall_score": (quality_score + efficiency_score) / 2,
            "completion_rate": completeness.completion_rate,
            "duration_days": timeline.duration_days,
            "peak_load": resources.peak_load
        }
    } 