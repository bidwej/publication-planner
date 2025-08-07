"""Constraint validation for schedules."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date, timedelta
import statistics
from models import Config, Submission, SubmissionType, ConferenceType, DeadlineValidation, DependencyValidation, ResourceValidation, DeadlineViolation, DependencyViolation, ResourceViolation, ConstraintValidationResult
from constants import PERFECT_COMPLIANCE_RATE, PERCENTAGE_MULTIPLIER, DAYS_PER_MONTH, DEFAULT_ABSTRACT_ADVANCE_DAYS, DEFAULT_POSTER_DURATION_DAYS


def is_working_day(check_date: date, blackout_dates: list[date] = None) -> bool:
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
    if not schedule:
        return DeadlineValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            compliance_rate=PERFECT_COMPLIANCE_RATE,
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
    
    compliance_rate = (compliant_submissions / total_submissions * PERCENTAGE_MULTIPLIER) if total_submissions > 0 else PERFECT_COMPLIANCE_RATE
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
            satisfaction_rate=PERFECT_COMPLIANCE_RATE,
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
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * PERCENTAGE_MULTIPLIER) if total_dependencies > 0 else PERFECT_COMPLIANCE_RATE
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
    # Check if blackout periods are enabled
    if config.scheduling_options and not config.scheduling_options.get("enable_blackout_periods", True):
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": PERFECT_COMPLIANCE_RATE,
            "summary": "Blackout periods disabled"
        }
    
    if not config.blackout_dates:
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": 100.0,
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
        duration_days = _get_submission_duration_days(sub, config)
        
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
    
    compliance_rate = (compliant_submissions / total_submissions * PERCENTAGE_MULTIPLIER) if total_submissions > 0 else PERFECT_COMPLIANCE_RATE
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions,
        "summary": f"Blackout dates: {compliant_submissions}/{total_submissions} submissions compliant ({compliance_rate:.1f}%)"
    }

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
        abstract_advance = config.scheduling_options.get("abstract_advance_days", DEFAULT_ABSTRACT_ADVANCE_DAYS)
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
    
    # Check conference response time
    if config.scheduling_options.get("conference_response_time_days"):
        response_time = config.scheduling_options["conference_response_time_days"]
        # Validate that submissions have enough time for conference response
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
            end_date = _get_submission_end_date(start_date, sub, config)
            response_deadline = deadline + timedelta(days=response_time)
            
            if end_date > response_deadline:
                violations.append({
                    "submission_id": sid,
                    "description": f"Paper {sid} may not meet conference response time ({response_time} days)",
                    "severity": "medium"
                })
    
    # Check working days only
    if config.scheduling_options.get("enable_working_days_only", False):
        for sid, start_date in schedule.items():
            if not is_working_day(start_date, config.blackout_dates):
                violations.append({
                    "submission_id": sid,
                    "description": f"Submission {sid} scheduled on non-working day {start_date}",
                    "severity": "low"
                })
    
    # Check priority weighting
    if config.scheduling_options.get("enable_priority_weighting", False):
        # This is validated in validate_priority_weighting function
        pass
    
    # Check dependency tracking
    if config.scheduling_options.get("enable_dependency_tracking", False):
        # This is validated in validate_dependency_satisfaction function
        pass
    
    # Check concurrency control
    if config.scheduling_options.get("enable_concurrency_control", False):
        # This is validated in validate_resource_constraints function
        pass
    
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
    
    compatibility_rate = (compatible_submissions / total_submissions * PERCENTAGE_MULTIPLIER) if total_submissions > 0 else PERFECT_COMPLIANCE_RATE
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
    
    for sid, start_date in schedule.items():
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
    
    compliance_rate = (compliant_mods / total_mods * PERCENTAGE_MULTIPLIER) if total_mods > 0 else PERFECT_COMPLIANCE_RATE
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
    for sid, start_date in schedule.items():
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
    
    compliance_rate = (compliant_papers / total_papers * PERCENTAGE_MULTIPLIER) if total_papers > 0 else PERFECT_COMPLIANCE_RATE
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_papers": total_papers,
        "compliant_papers": compliant_papers,
        "summary": f"Paper lead time: {compliant_papers}/{total_papers} papers use config default ({compliance_rate:.1f}%)"
    }


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
            return sub.draft_window_months * DAYS_PER_MONTH
        else:
            return DEFAULT_POSTER_DURATION_DAYS  # Default 1 month for posters
    else:  # SubmissionType.PAPER
        # Use draft_window_months if available, otherwise fall back to config
        if sub.draft_window_months > 0:
            return sub.draft_window_months * DAYS_PER_MONTH
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
    
    deadline = conf.deadlines[sub.kind]
    if deadline is None:
        return True  # No deadline set
    
    end_date = _get_submission_end_date(start_date, sub, config)
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
    from scoring.penalty import calculate_penalty_score
    from scoring.quality import calculate_quality_score
    from scoring.efficiency import calculate_efficiency_score
    from output.analytics import (
        analyze_schedule_completeness,
        analyze_schedule_distribution,
        analyze_submission_types,
        analyze_timeline,
        analyze_resources
    )
    
    # 1. Constraint validation
    constraint_result = validate_all_constraints_comprehensive(schedule, config)
    
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
        "deadline_compliance": constraint_result["summary"]["deadline_compliance"],
        "dependency_satisfaction": constraint_result["summary"]["dependency_satisfaction"],
        "resource_valid": constraint_result["summary"]["resource_valid"],
        "blackout_compliant": constraint_result["summary"]["blackout_compliant"],
        "scheduling_options_valid": constraint_result["summary"]["scheduling_options_valid"],
        "conference_compatible": constraint_result["summary"]["conference_compatible"],
        "single_conference_valid": constraint_result["summary"]["single_conference_valid"],
        "soft_block_compliant": constraint_result["summary"]["soft_block_compliant"],
        "overall_valid": constraint_result["summary"]["overall_valid"],
        
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
            "is_feasible": constraint_result["summary"]["overall_valid"],
            "total_violations": constraint_result["total_violations"],
            "overall_score": (quality_score + efficiency_score) / 2,
            "completion_rate": completeness.completion_rate,
            "duration_days": timeline.duration_days,
            "peak_load": resources.peak_load
        }
    } 