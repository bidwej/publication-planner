"""Constraint validation for schedules."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date, timedelta
from .models import Config, Submission, SubmissionType, DeadlineValidation, DependencyValidation, ResourceValidation, DeadlineViolation, DependencyViolation, ResourceViolation

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
        end_date = _get_submission_end_date(start_date, sub, config)
        
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
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Calculate duration using proper logic
        end_date = _get_submission_end_date(start_date, sub, config)
        duration_days = (end_date - start_date).days
        
        # Add workload for each day
        for i in range(duration_days + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
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

def validate_all_constraints(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate all constraints for a schedule."""
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    return {
        "deadlines": deadline_validation,
        "dependencies": dependency_validation,
        "resources": resource_validation,
        "is_valid": (deadline_validation.is_valid and 
                     dependency_validation.is_valid and 
                     resource_validation.is_valid)
    }

def _get_submission_end_date(start_date: date, sub: Submission, config: Config) -> date:
    """Calculate the end date for a submission using proper duration logic."""
    if sub.kind == SubmissionType.ABSTRACT:
        return start_date
    else:
        # Use draft_window_months if available, otherwise fall back to config
        if sub.draft_window_months > 0:
            # Approximate months as 30 days each
            duration_days = sub.draft_window_months * 30
        else:
            duration_days = config.min_paper_lead_time_days
        return start_date + timedelta(days=duration_days) 