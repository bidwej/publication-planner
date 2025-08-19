"""Resource constraint validation for schedule feasibility."""

from typing import Dict, Any, List
from datetime import date, timedelta

from src.core.models import Config, ResourceViolation, Schedule, ValidationResult, ConstraintViolation
from src.core.constants import QUALITY_CONSTANTS


def validate_resources_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate resource constraints for concurrent submission limits and preferred timing."""
    if not schedule:
        return ValidationResult(
            is_valid=True, 
            violations=[], 
            summary="No schedule to validate",
            metadata={
                "max_concurrent": config.max_concurrent_submissions,
                "max_observed": 0, 
                "total_days": 0
            }
        )
    
    # Validate concurrent submission limits
    concurrent_result = _validate_concurrent_submissions(schedule, config)
    
    # Validate author submission limits per conference
    author_result = _validate_author_submission_limits(schedule, config)
    
    # Validate preferred timing constraints (soft block model)
    timing_result = _validate_preferred_timing(schedule, config)
    
    # Combine violations
    all_violations = concurrent_result.violations + author_result.violations + timing_result.violations
    is_valid = len(all_violations) == 0
    
    # Create combined summary
    concurrent_summary = concurrent_result.summary
    timing_summary = timing_result.summary
    combined_summary = f"{concurrent_summary}; {timing_summary}" if timing_summary else concurrent_summary
    
    return ValidationResult(
        is_valid=is_valid, 
        violations=all_violations,
        summary=combined_summary,
        metadata={
            "max_concurrent": config.max_concurrent_submissions,
            "max_observed": concurrent_result.metadata.get("max_observed", 0), 
            "total_days": concurrent_result.metadata.get("total_days", 0),
            "author_limits": author_result.metadata.get("conferences_with_limits", 0)
        }
    )


def _validate_concurrent_submissions(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate concurrent submission limits."""
    violations = []
    daily_load = _calculate_daily_load(schedule, config)
    
    # Check for violations
    max_observed = max(daily_load.values()) if daily_load else 0
    total_days = len(daily_load)
    
    if max_observed > config.max_concurrent_submissions:
        # Find dates with violations
        for check_date, load in daily_load.items():
            if load > config.max_concurrent_submissions:
                violations.append(ResourceViolation(
                    submission_id="resource_constraint",  # Dummy ID for resource violations
                    date=check_date, 
                    description=f"Date {check_date} has {load} concurrent submissions (max {config.max_concurrent_submissions})",
                    severity="high", 
                    load=load, 
                    limit=config.max_concurrent_submissions, 
                    excess=load - config.max_concurrent_submissions
                ))
    
    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        summary=f"Max concurrent submissions: {max_observed}/{config.max_concurrent_submissions}",
        metadata={
            "max_observed": max_observed,
            "total_days": total_days
        }
    )


def _validate_author_submission_limits(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate that authors don't exceed submission limits per conference."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    # Group submissions by conference and author
    conference_author_counts = {}
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.conference_id or not sub.author:
            continue
        
        total_submissions += 1
        conf = config.get_conference(sub.conference_id)
        if not conf or not conf.max_submissions_per_author:
            compliant_submissions += 1
            continue
        
        # Count submissions per author per conference
        key = (sub.conference_id, sub.author)
        if key not in conference_author_counts:
            conference_author_counts[key] = 0
        conference_author_counts[key] += 1
        
        # Check if limit exceeded
        if conference_author_counts[key] > conf.max_submissions_per_author:
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Author {sub.author} has {conference_author_counts[key]} submissions to {sub.conference_id} (limit: {conf.max_submissions_per_author})",
                severity="high"
            ))
        else:
            compliant_submissions += 1
    
    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        summary=f"Author submission limits: {compliant_submissions}/{total_submissions} compliant",
        metadata={
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions,
            "conferences_with_limits": len([c for c in config.conferences if c.max_submissions_per_author])
        }
    )


def _validate_preferred_timing(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate preferred timing constraints (soft block model - PCCP)."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.earliest_start_date:
            continue
        
        total_submissions += 1
        days_diff = abs((interval.start_date - sub.earliest_start_date).days)
        
        if days_diff > 60:  # ±2 months (60 days) preferred window
            violations.append(ConstraintViolation(
                submission_id=sid, 
                description=f"Submission scheduled {days_diff} days from earliest start date (preferred: ±60 days)",
                severity="medium"
            ))
        else:
            compliant_submissions += 1
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions within preferred timing constraints",
        metadata={
            "total_submissions": total_submissions, 
            "compliant_submissions": compliant_submissions
        }
    )


def _calculate_daily_load(schedule: Schedule, config: Config) -> Dict[date, int]:
    """Calculate daily resource load from schedule."""
    daily_load = {}
    
    for sid, interval in schedule.intervals.items():
        submission = config.get_submission(sid)
        if not submission:
            continue
        
        duration = submission.get_duration_days(config)
        for i in range(duration):
            check_date = interval.start_date + timedelta(days=i)
            daily_load[check_date] = daily_load.get(check_date, 0) + 1
    
    return daily_load


def _validate_peak_load(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate peak load constraints."""
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return ValidationResult(
            is_valid=True, 
            violations=[],
            summary="No daily load data",
            metadata={
                "peak_load": 0, 
                "max_allowed": config.max_concurrent_submissions
            }
        )
    
    peak_load = max(daily_load.values())
    is_valid = peak_load <= config.max_concurrent_submissions
    
    return ValidationResult(
        is_valid=is_valid,
        violations=[] if is_valid else [ConstraintViolation(
            submission_id="",
            description=f"Peak load {peak_load} exceeds maximum allowed {config.max_concurrent_submissions}",
            severity="high"
        )],
        summary=f"Peak load: {peak_load}/{config.max_concurrent_submissions}",
        metadata={
            "peak_load": peak_load, 
            "max_allowed": config.max_concurrent_submissions
        }
    )


def _validate_average_load(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate average load constraints."""
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return ValidationResult(
            is_valid=True, 
            violations=[],
            summary="No daily load data",
            metadata={
                "average_load": 0.0
            }
        )
    
    total_load = sum(daily_load.values())
    average_load = total_load / len(daily_load)
    
    # Check if average load is reasonable (e.g., not too close to max)
    max_load = config.max_concurrent_submissions
    threshold = max_load * 0.8  # 80% of max capacity
    
    is_valid = average_load <= threshold
    
    return ValidationResult(
        is_valid=is_valid,
        violations=[] if is_valid else [ConstraintViolation(
            submission_id="",
            description=f"Average load {average_load:.2f} exceeds threshold {threshold:.2f}",
            severity="medium"
        )],
        summary=f"Average load: {average_load:.2f}/{threshold:.2f}",
        metadata={
            "average_load": average_load,
            "threshold": threshold,
            "max_capacity": max_load
        }
    )
