"""Constraint validation for the Endoscope AI project."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import date, timedelta
import statistics
from src.core.models import Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceSubmissionType, DeadlineValidation, DeadlineViolation, DependencyValidation, DependencyViolation, ResourceValidation, ResourceViolation, ConstraintValidationResult
from src.core.constants import (
    EFFICIENCY_CONSTANTS, 
    QUALITY_CONSTANTS, 
    SCORING_CONSTANTS, 
    REPORT_CONSTANTS, 
    SCHEDULING_CONSTANTS,
    ANALYTICS_CONSTANTS
)


def is_working_day(check_date: date, blackout_dates: list[date] | None = None) -> bool:
    """
    Check if a date is a working day (not weekend or blackout).
    
    Args:
        check_date: Date to check
        blackout_dates: List of blackout dates (weekends, holidays, etc.)
        
    Returns:
        True if it's a working day, False otherwise
    """
    if blackout_dates is None:
        blackout_dates = []
    
    # Check if it's a weekend
    if check_date.weekday() in [5, 6]:  # Saturday, Sunday
        return False
    
    # Check if it's in the blackout dates
    if check_date in blackout_dates:
        return False
    
    return True


def validate_deadline_compliance(schedule: Dict[str, date], config: Config) -> DeadlineValidation:
    """Validate that all submissions meet their deadlines."""
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DeadlineValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            compliance_rate=perfect_compliance_rate,
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
        
        # Calculate end date using submission method
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
    
    # Calculate compliance rate
    compliance_rate = (compliant_submissions / total_submissions * percentage_multiplier) if total_submissions > 0 else perfect_compliance_rate
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
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DependencyValidation(
            is_valid=True,
            violations=[],
            summary="No dependencies to validate",
            satisfaction_rate=perfect_compliance_rate,
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
            
            # Calculate dependency end date using submission method
            dep_end = dep_sub.get_end_date(dep_start, config)
            
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
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * percentage_multiplier) if total_dependencies > 0 else perfect_compliance_rate
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

def validate_blackout_dates(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that no submissions are scheduled on blackout dates."""
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    # Check if blackout periods are enabled
    if config.scheduling_options and not config.scheduling_options.get("enable_blackout_periods", True):
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": perfect_compliance_rate,
            "summary": "Blackout periods disabled"
        }
    
    if not config.blackout_dates:
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": QUALITY_CONSTANTS.perfect_compliance_rate,
            "summary": "No blackout dates configured"
        }
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        duration_days = sub.get_duration_days(config)
        
        # Check each day of the submission
        submission_violations = []
        for i in range(duration_days + 1):
            check_date = start_date + timedelta(days=i)
            if check_date in config.blackout_dates:
                submission_violations.append(check_date)
        
        if submission_violations:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} scheduled on blackout dates: {submission_violations}",
                "severity": "medium",
                "blackout_dates": submission_violations
            })
        else:
            compliant_submissions += 1
    
    compliance_rate = (compliant_submissions / total_submissions * percentage_multiplier) if total_submissions > 0 else perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions,
        "summary": f"Blackout dates: {compliant_submissions}/{total_submissions} submissions compliant ({compliance_rate:.1f}%)"
    }

def _validate_early_abstract_scheduling(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate early abstract scheduling."""
    violations = []
    
    # Check if scheduling_options exists before accessing it
    if not config.scheduling_options:
        return violations
    
    abstract_advance = config.scheduling_options.get("abstract_advance_days", SCHEDULING_CONSTANTS.abstract_advance_days)
    abstracts = [sid for sid, sub in config.submissions_dict.items() 
                if sub.kind == SubmissionType.ABSTRACT]
    
    for abstract_id in abstracts:
        if abstract_id not in schedule:
            continue
        
        sub = config.submissions_dict[abstract_id]
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if SubmissionType.ABSTRACT not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[SubmissionType.ABSTRACT]
        early_date = deadline - timedelta(days=abstract_advance)
        scheduled_date = schedule[abstract_id]
        
        if scheduled_date > early_date:
            violations.append({
                "submission_id": abstract_id,
                "description": f"Abstract {abstract_id} not scheduled early enough (should be {early_date}, scheduled {scheduled_date})",
                "severity": "low"
            })
    
    return violations


def _validate_conference_response_time(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate conference response time."""
    violations = []
    
    # Check if scheduling_options exists and has the required key
    if not config.scheduling_options or "conference_response_time_days" not in config.scheduling_options:
        return violations
    
    response_time = config.scheduling_options["conference_response_time_days"]
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if SubmissionType.PAPER not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[SubmissionType.PAPER]
        end_date = sub.get_end_date(start_date, config)
        response_deadline = deadline + timedelta(days=response_time)
        
        if end_date > response_deadline:
            violations.append({
                "submission_id": sid,
                "description": f"Paper {sid} may not meet conference response time ({response_time} days)",
                "severity": "medium"
            })
    
    return violations


def _validate_working_days_only(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate working days only scheduling."""
    violations = []
    
    for sid, start_date in schedule.items():
        if not is_working_day(start_date, config.blackout_dates):
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} scheduled on non-working day {start_date}",
                "severity": "low"
            })
    
    return violations


def validate_scheduling_options(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that scheduling options are respected."""
    if not config.scheduling_options:
        return {
            "is_valid": True,
            "violations": [],
            "summary": "No scheduling options configured"
        }
    
    violations = []
    
    # Check early abstract scheduling
    if config.scheduling_options.get("enable_early_abstract_scheduling", False):
        violations.extend(_validate_early_abstract_scheduling(schedule, config))
    
    # Check conference response time
    if config.scheduling_options.get("conference_response_time_days"):
        violations.extend(_validate_conference_response_time(schedule, config))
    
    # Check working days only
    if config.scheduling_options.get("enable_working_days_only", False):
        violations.extend(_validate_working_days_only(schedule, config))
    

    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"Scheduling options: {'Valid' if is_valid else f'{len(violations)} violations'}"
    }

def validate_conference_compatibility(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that submissions are compatible with their conference venues."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, _ in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} references unknown conference {sub.conference_id}",
                "severity": "high"
            })
            continue
        
        # Check medical vs engineering compatibility
        if sub.engineering and conf.conf_type == ConferenceType.MEDICAL:
            # Engineering papers can go to medical conferences (allowed)
            compatible_submissions += 1
        elif not sub.engineering and conf.conf_type == ConferenceType.ENGINEERING:
            # Medical papers cannot go to engineering conferences
            violations.append({
                "submission_id": sid,
                "description": f"Medical paper {sid} assigned to engineering conference {sub.conference_id}",
                "severity": "high"
            })
        else:
            # Compatible assignment
            compatible_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compatibility_rate": compatibility_rate,
        "total_submissions": total_submissions,
        "compatible_submissions": compatible_submissions,
        "summary": f"{compatible_submissions}/{total_submissions} submissions have compatible venues ({compatibility_rate:.1f}%)"
    }

def validate_single_conference_policy(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that each paper is submitted to only one venue per annual cycle."""
    violations = []
    paper_conferences = {}
    
    for sid, _ in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        if not sub.conference_id:
            continue
        
        # Group by paper ID (remove -pap suffix)
        paper_id = sid.replace("-pap", "")
        if paper_id in paper_conferences:
            if paper_conferences[paper_id] != sub.conference_id:
                violations.append({
                    "submission_id": sid,
                    "description": f"Paper {paper_id} assigned to multiple conferences: {paper_conferences[paper_id]} and {sub.conference_id}",
                    "severity": "medium"
                })
        else:
            paper_conferences[paper_id] = sub.conference_id
    
    # Calculate compliance rate using constants from constants.py
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "total_papers": len(paper_conferences),
        "summary": f"Single conference policy: {'Valid' if is_valid else f'{len(violations)} violations'}"
    }

def validate_soft_block_model(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate soft block model for PCCP modifications (±2 months with penalties)."""
    violations = []
    total_mods = 0
    compliant_mods = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sid.endswith("-wrk"):  # Only check mods
            continue
        
        total_mods += 1
        if sub.earliest_start_date is None:
            continue
        
        # Check if mod is within ±2 months of earliest start date
        months_diff = abs((start_date.year - sub.earliest_start_date.year) * 12 + 
                         (start_date.month - sub.earliest_start_date.month))
        
        if months_diff <= 2:
            compliant_mods += 1
        else:
            violations.append({
                "submission_id": sid,
                "description": f"Mod {sid} scheduled {months_diff} months from earliest start date (limit: ±2 months)",
                "severity": "medium",
                "months_deviation": months_diff
            })
    
    # Calculate compliance rate using constants from constants.py
    compliance_rate = (compliant_mods / total_mods * QUALITY_CONSTANTS.percentage_multiplier) if total_mods > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_mods": total_mods,
        "compliant_mods": compliant_mods,
        "summary": f"Soft block model: {compliant_mods}/{total_mods} mods within ±2 months ({compliance_rate:.1f}%)"
    }

def validate_priority_weighting(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that priority weighting is being applied correctly."""
    if not config.priority_weights:
        return {
            "is_valid": True,
            "summary": "No priority weights configured"
        }
    
    # Calculate actual priority scores for scheduled submissions
    actual_priorities = []
    for sid, _ in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Determine priority based on submission type and engineering flag
        if sub.kind == SubmissionType.PAPER:
            if sub.engineering:
                priority = config.priority_weights.get("engineering_paper", 2.0)
            else:
                priority = config.priority_weights.get("medical_paper", 1.0)
        elif sub.kind == SubmissionType.ABSTRACT:
            priority = config.priority_weights.get("abstract", 0.5)
        else:
            priority = config.priority_weights.get("mod", 1.5)
        
        actual_priorities.append({
            "submission_id": sid,
            "priority": priority,
            "submission_type": sub.kind.value,
            "engineering": sub.engineering
        })
    
    # Calculate average priority for summary
    avg_priority = statistics.mean(p["priority"] for p in actual_priorities) if actual_priorities else 0
    
    return {
        "is_valid": True,
        "actual_priorities": actual_priorities,
        "average_priority": avg_priority,
        "total_submissions": len(actual_priorities),
        "summary": f"Priority weighting: avg={avg_priority:.2f} across {len(actual_priorities)} submissions"
    }

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

def validate_all_constraints_comprehensive(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate all constraints including the new ones from README."""
    # Core constraints
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    # Additional constraints from README
    blackout_validation = validate_blackout_dates(schedule, config)
    scheduling_options_validation = validate_scheduling_options(schedule, config)
    conference_compatibility = validate_conference_compatibility(schedule, config)
    conference_submission_compatibility = validate_conference_submission_compatibility(schedule, config)
    abstract_paper_dependencies = validate_abstract_paper_dependencies(schedule, config)
    single_conference_policy = validate_single_conference_policy(schedule, config)
    soft_block_model = validate_soft_block_model(schedule, config)
    priority_weighting = validate_priority_weighting(schedule, config)
    paper_lead_time_validation = validate_paper_lead_time_months(schedule, config)
    
    # Overall validity
    is_valid = (deadline_validation.is_valid and 
                dependency_validation.is_valid and 
                resource_validation.is_valid and
                blackout_validation["is_valid"] and
                scheduling_options_validation["is_valid"] and
                conference_compatibility["is_valid"] and
                conference_submission_compatibility["is_valid"] and
                abstract_paper_dependencies["is_valid"] and
                single_conference_policy["is_valid"] and
                soft_block_model["is_valid"] and
                paper_lead_time_validation["is_valid"])
    
    return {
        # Core constraints
        "deadlines": deadline_validation,
        "dependencies": dependency_validation,
        "resources": resource_validation,
        
        # Additional constraints
        "blackout_dates": blackout_validation,
        "scheduling_options": scheduling_options_validation,
        "conference_compatibility": conference_compatibility,
        "conference_submission_compatibility": conference_submission_compatibility,
        "abstract_paper_dependencies": abstract_paper_dependencies,
        "single_conference_policy": single_conference_policy,
        "soft_block_model": soft_block_model,
        "priority_weighting": priority_weighting,
        "paper_lead_time": paper_lead_time_validation,
        
        # Overall
        "is_valid": is_valid,
                 "total_violations": (
             len(deadline_validation.violations) +
             len(dependency_validation.violations) +
             len(resource_validation.violations) +
             len(blackout_validation["violations"]) +
             len(scheduling_options_validation["violations"]) +
             len(conference_compatibility["violations"]) +
             len(conference_submission_compatibility["violations"]) +
             len(abstract_paper_dependencies["violations"]) +
             len(single_conference_policy["violations"]) +
             len(soft_block_model["violations"]) +
             len(paper_lead_time_validation["violations"])
         ),
        "summary": {
            "deadline_compliance": deadline_validation.compliance_rate,
            "dependency_satisfaction": dependency_validation.satisfaction_rate,
            "resource_valid": resource_validation.is_valid,
            "blackout_compliant": blackout_validation["compliance_rate"],
            "scheduling_options_valid": scheduling_options_validation["is_valid"],
            "conference_compatible": conference_compatibility["compatibility_rate"],
            "conference_submission_compatible": conference_submission_compatibility["compatibility_rate"],
            "abstract_paper_dependencies_valid": abstract_paper_dependencies["dependency_rate"],
            "single_conference_valid": single_conference_policy["is_valid"],
            "soft_block_compliant": soft_block_model["compliance_rate"],
            "paper_lead_time_compliant": paper_lead_time_validation["compliance_rate"],
            "overall_valid": is_valid
        }
    }

def validate_paper_lead_time_months(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that papers use the correct lead time months from config."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        total_papers += 1
        
        # Check if paper uses the correct draft_window_months
        expected_months = config.default_paper_lead_time_months
        actual_months = sub.draft_window_months
        
        if actual_months != expected_months:
            violations.append({
                "submission_id": sid,
                "description": f"Paper {sid} uses {actual_months} months instead of config default {expected_months} months",
                "severity": "low",
                "expected_months": expected_months,
                "actual_months": actual_months
            })
        else:
            compliant_papers += 1
    
    # Calculate compliance rate using constants from constants.py
    compliance_rate = (compliant_papers / total_papers * QUALITY_CONSTANTS.percentage_multiplier) if total_papers > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_papers": total_papers,
        "compliant_papers": compliant_papers,
        "summary": f"Paper lead time: {compliant_papers}/{total_papers} papers use config default ({compliance_rate:.1f}%)"
    }

def validate_conference_submission_compatibility(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that submissions are compatible with their conference submission types."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} references unknown conference {sub.conference_id}",
                "severity": "high"
            })
            continue
        
        # Check if conference accepts this submission type
        if not conf.accepts_submission_type(sub.kind):
            submission_type_str = conf.submission_types.value if conf.submission_types else "unknown"
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} ({sub.kind.value}) not accepted by conference {sub.conference_id} ({submission_type_str})",
                "severity": "high",
                "submission_type": sub.kind.value,
                "conference_submission_type": submission_type_str
            })
            continue
        
        # Check abstract-to-paper dependencies
        if sub.kind == SubmissionType.PAPER and conf.requires_abstract_before_paper():
            # Find the corresponding abstract submission using utility function
            from src.core.models import generate_abstract_id
            abstract_id = generate_abstract_id(sid, conf.id)
            if abstract_id not in schedule:
                violations.append({
                    "submission_id": sid,
                    "description": f"Paper {sid} requires abstract submission {abstract_id} but it's not scheduled",
                    "severity": "high",
                    "missing_dependency": abstract_id
                })
                continue
            
            # Check if abstract is scheduled before paper
            abstract_start = schedule[abstract_id]
            if abstract_start >= start_date:
                violations.append({
                    "submission_id": sid,
                    "description": f"Paper {sid} scheduled before required abstract {abstract_id}",
                    "severity": "high",
                    "abstract_id": abstract_id,
                    "paper_start": start_date,
                    "abstract_start": abstract_start
                })
                continue
        
        compatible_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compatibility_rate": compatibility_rate,
        "total_submissions": total_submissions,
        "compatible_submissions": compatible_submissions,
        "summary": f"Conference submission compatibility: {compatible_submissions}/{total_submissions} submissions compatible ({compatibility_rate:.1f}%)"
    }


def validate_abstract_paper_dependencies(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate abstract-paper dependency relationships."""
    violations = []
    total_papers = 0
    valid_papers = 0
    
    for sid in schedule:
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER or not sub.conference_id:
            continue
        
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf or not conf.requires_abstract_before_paper():
            continue
        
        total_papers += 1
        
        # Check if required abstract exists and is scheduled
        from src.core.models import generate_abstract_id
        abstract_id = generate_abstract_id(sub.id, sub.conference_id)
        abstract = config.submissions_dict.get(abstract_id)
        
        if not abstract:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "missing_abstract_id": abstract_id,
                "description": f"Paper {sid} requires abstract {abstract_id} for conference {sub.conference_id}"
            })
            continue
        
        if abstract_id not in schedule:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "missing_abstract_id": abstract_id,
                "description": f"Paper {sid} requires abstract {abstract_id} to be scheduled"
            })
            continue
        
        # Check if paper is scheduled after abstract
        paper_start = schedule[sid]
        abstract_start = schedule[abstract_id]
        
        if paper_start <= abstract_start:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "abstract_id": abstract_id,
                "paper_start": paper_start.isoformat(),
                "abstract_start": abstract_start.isoformat(),
                "description": f"Paper {sid} must be scheduled after abstract {abstract_id}"
            })
            continue
        
        # Check if paper depends on abstract
        if abstract_id not in (sub.depends_on or []):
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "abstract_id": abstract_id,
                "description": f"Paper {sid} must depend on abstract {abstract_id}"
            })
            continue
        
        valid_papers += 1
    
    dependency_rate = (valid_papers / total_papers * QUALITY_CONSTANTS.percentage_multiplier) if total_papers > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "dependency_rate": dependency_rate,
        "total_papers": total_papers,
        "valid_papers": valid_papers,
        "summary": f"Abstract-paper dependencies: {valid_papers}/{total_papers} papers valid ({dependency_rate:.1f}%)"
    }





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
        
        duration_days = sub.get_duration_days(config)
        
        # Add load for each day the submission is active
        for i in range(duration_days + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    return daily_load


def _get_next_deadline(conference: 'Conference', submission_type: SubmissionType, current_date: date) -> Optional[date]:
    """
    Get the next available deadline for a recurring conference.
    
    Parameters
    ----------
    conference : Conference
        The conference to check
    submission_type : SubmissionType
        The type of submission
    current_date : date
        The current date to calculate from
        
    Returns
    -------
    Optional[date]
        The next deadline, or None if no deadline exists
    """
    if submission_type not in conference.deadlines:
        return None
    
    base_deadline = conference.deadlines[submission_type]
    if base_deadline is None:
        return None
    
    # If current date is before or equal to base deadline, use base deadline
    if current_date <= base_deadline:
        return base_deadline
    
    # Calculate next deadline based on recurrence
    if conference.recurrence.value == "annual":
        # Add years until we find a deadline after current_date
        next_deadline = base_deadline
        while next_deadline <= current_date:
            next_deadline = date(next_deadline.year + 1, next_deadline.month, next_deadline.day)
        return next_deadline
    elif conference.recurrence.value == "biennial":
        # Add 2 years until we find a deadline after current_date
        next_deadline = base_deadline
        while next_deadline <= current_date:
            next_deadline = date(next_deadline.year + 2, next_deadline.month, next_deadline.day)
        return next_deadline
    elif conference.recurrence.value == "quarterly":
        # Add 3 months until we find a deadline after current_date
        next_deadline = base_deadline
        while next_deadline <= current_date:
            # Add 3 months
            if next_deadline.month <= 9:
                next_deadline = date(next_deadline.year, next_deadline.month + 3, next_deadline.day)
            else:
                next_deadline = date(next_deadline.year + 1, next_deadline.month - 9, next_deadline.day)
        return next_deadline
    else:
        # Unknown recurrence, return base deadline
        return base_deadline


def validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """
    Validate if a submission starting on the given date meets its deadline.
    
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
    
    # Get the next available deadline (handles recurring conferences)
    deadline = _get_next_deadline(conf, sub.kind, start_date)
    if deadline is None:
        return True  # No deadline set
    
    end_date = sub.get_end_date(start_date, config)
    return end_date <= deadline


def validate_deadline_with_lookahead(sub: Submission, start: date, config: Config, 
                                   conferences: Dict[str, Any], lookahead_days: int = 0) -> bool:
    """Validate if starting on this date meets the deadline with optional lookahead buffer."""
    # Use the unified deadline checking logic
    base_compliance = validate_deadline_compliance_single(start, sub, config)
    
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


def validate_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                                 submissions: Dict[str, Submission], config: Config, current: date) -> bool:
    """Validate if all dependencies are satisfied."""
    if not sub.depends_on:
        return True
    for dep_id in sub.depends_on:
        if dep_id not in schedule:
            return False
        dep_end = submissions[dep_id].get_end_date(schedule[dep_id], config)
        if current < dep_end + timedelta(days=sub.lead_time_from_parents):
            return False
    return True


def validate_venue_compatibility(submissions: Dict[str, Submission], conferences: Dict[str, Any]) -> None:
    """Validate that submissions are compatible with their venues."""
    for sid, submission in submissions.items():
        if submission.conference_id and submission.conference_id not in conferences:
            raise ValueError(f"Submission {sid} references unknown conference {submission.conference_id}")


def _calculate_comprehensive_scores(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Calculate all scoring metrics for a schedule."""
    from scoring.penalty import calculate_penalty_score
    from scoring.quality import calculate_quality_score
    from scoring.efficiency import calculate_efficiency_score
    
    penalty_breakdown = calculate_penalty_score(schedule, config)
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    
    return {
        "penalty": penalty_breakdown,
        "quality_score": quality_score,
        "efficiency_score": efficiency_score,
        "total_penalty": penalty_breakdown.total_penalty
    }


def _calculate_comprehensive_analytics(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Calculate all analytics for a schedule."""
    from output.analytics import (
        analyze_schedule_completeness,
        analyze_schedule_distribution,
        analyze_submission_types,
        analyze_timeline,
        analyze_resources
    )
    
    completeness = analyze_schedule_completeness(schedule, config)
    distribution = analyze_schedule_distribution(schedule, config)
    types_analysis = analyze_submission_types(schedule, config)
    timeline = analyze_timeline(schedule, config)
    resources = analyze_resources(schedule, config)
    
    return {
        "completeness": completeness,
        "distribution": distribution,
        "types": types_analysis,
        "timeline": timeline,
        "resources": resources,
        "completion_rate": completeness.completion_rate,
        "duration_days": timeline.duration_days,
        "peak_load": resources.peak_load
    }


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
    # 1. Constraint validation
    constraint_result = validate_all_constraints_comprehensive(schedule, config)
    
    # 2. Scoring calculations
    scores = _calculate_comprehensive_scores(schedule, config)
    
    # 3. Analytics
    analytics = _calculate_comprehensive_analytics(schedule, config)
    
    # 4. Build result
    summary = constraint_result["summary"]
    overall_score = (scores["quality_score"] + scores["efficiency_score"]) / 2
    
    return {
        # Constraints
        "constraints": constraint_result,
        "deadline_compliance": summary["deadline_compliance"],
        "dependency_satisfaction": summary["dependency_satisfaction"],
        "resource_valid": summary["resource_valid"],
        "blackout_compliant": summary["blackout_compliant"],
        "scheduling_options_valid": summary["scheduling_options_valid"],
        "conference_compatible": summary["conference_compatible"],
        "single_conference_valid": summary["single_conference_valid"],
        "soft_block_compliant": summary["soft_block_compliant"],
        "overall_valid": summary["overall_valid"],
        
        # Scoring
        **scores,
        
        # Analytics
        **analytics,
        
        # Summary
        "summary": {
            "is_feasible": summary["overall_valid"],
            "total_violations": constraint_result["total_violations"],
            "overall_score": overall_score,
            "completion_rate": analytics["completion_rate"],
            "duration_days": analytics["duration_days"],
            "peak_load": analytics["peak_load"]
        }
    }


def validate_single_submission_constraints(submission: Submission, start_date: date, schedule: Dict[str, date], config: Config) -> bool:
    """
    Validate all constraints for a single submission at a given start date.
    
    Parameters
    ----------
    submission : Submission
        The submission to validate
    start_date : date
        The proposed start date
    schedule : Dict[str, date]
        Current schedule (may be empty for first submission)
    config : Config
        Configuration object
        
    Returns
    -------
    bool
        True if all constraints are satisfied, False otherwise
    """
    # Create a temporary schedule with this submission
    temp_schedule = schedule.copy()
    temp_schedule[submission.id] = start_date
    
    # Basic deadline check
    if not validate_deadline_compliance_single(start_date, submission, config):
        return False
    
    # Dependencies check
    if not validate_dependencies_satisfied(submission, schedule, config.submissions_dict, config, start_date):
        return False
    
    # Advanced constraints - call comprehensive validation functions
    # Soft block model validation
    soft_block_result = validate_soft_block_model(temp_schedule, config)
    if not soft_block_result.get("is_valid", True):
        return False
    
    # Working days validation
    working_days_result = validate_scheduling_options(temp_schedule, config)
    if not working_days_result.get("is_valid", True):
        return False
    
    # Single conference policy validation
    single_conf_result = validate_single_conference_policy(temp_schedule, config)
    if not single_conf_result.get("is_valid", True):
        return False
    
    # Blackout dates validation
    blackout_result = validate_blackout_dates(temp_schedule, config)
    if not blackout_result.get("is_valid", True):
        return False
    
    # Conference compatibility validation
    conf_compat_result = validate_conference_compatibility(temp_schedule, config)
    if not conf_compat_result.get("is_valid", True):
        return False
    
    # Conference submission compatibility validation
    conf_sub_compat_result = validate_conference_submission_compatibility(temp_schedule, config)
    if not conf_sub_compat_result.get("is_valid", True):
        return False
    
    # Abstract-paper dependencies validation
    abstract_paper_result = validate_abstract_paper_dependencies(temp_schedule, config)
    if not abstract_paper_result.get("is_valid", True):
        return False
    
    # Paper lead time months validation
    lead_time_result = validate_paper_lead_time_months(temp_schedule, config)
    if not lead_time_result.get("is_valid", True):
        return False
    
    # Direct conference compatibility check
    if submission.conference_id and submission.conference_id in config.conferences_dict:
        conf = config.conferences_dict[submission.conference_id]
        if not conf.accepts_submission_type(submission.kind):
            return False
    
    return True 