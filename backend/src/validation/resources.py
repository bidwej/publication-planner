"""Resource validation functions for concurrent submission limits and preferred timing constraints."""

from typing import Dict, Any
from datetime import date, timedelta

from ..core.models import Config, ResourceValidation, ResourceViolation, Schedule
from ..core.constants import QUALITY_CONSTANTS


def validate_resources_constraints(schedule: Schedule, config: Config) -> ResourceValidation:
    """Validate resource constraints for concurrent submissions and preferred timing."""
    if not schedule:
        return ResourceValidation(is_valid=True, violations=[], summary="No schedule to validate",
                                max_observed=0, total_days=0)
    
    # Validate concurrent submission limits
    concurrent_result = _validate_concurrent_submissions(schedule, config)
    
    # Validate preferred timing constraints (soft block model)
    timing_result = _validate_preferred_timing(schedule, config)
    
    # Combine violations
    all_violations = concurrent_result.get("violations", []) + timing_result.get("violations", [])
    is_valid = len(all_violations) == 0
    
    # Create combined summary
    concurrent_summary = concurrent_result.get("summary", "")
    timing_summary = timing_result.get("summary", "")
    combined_summary = f"{concurrent_summary}; {timing_summary}" if timing_summary else concurrent_summary
    
    return ResourceValidation(
        is_valid=is_valid, violations=all_violations,
        summary=combined_summary,
        max_observed=concurrent_result.get("max_observed", 0), 
        total_days=concurrent_result.get("total_days", 0)
    )


def _validate_concurrent_submissions(schedule: Schedule, config: Config) -> Dict[str, Any]:
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
                    date=check_date, description=f"Date {check_date} has {load} concurrent submissions (max {config.max_concurrent_submissions})",
                    severity="high", concurrent_count=load, max_allowed=config.max_concurrent_submissions
                ))
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "summary": f"Max concurrent submissions: {max_observed}/{config.max_concurrent_submissions}",
        "max_observed": max_observed,
        "total_days": total_days
    }


def _validate_preferred_timing(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate preferred timing constraints (soft block model - PCCP)."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.earliest_start_date:
            continue
        
        total_submissions += 1
        days_diff = abs((interval.start_date - sub.earliest_start_date).days)
        
        if days_diff > 60:  # ±2 months (60 days) preferred window
            violations.append({
                "submission_id": sid, 
                "description": f"Submission scheduled {days_diff} days from earliest start date (preferred: ±60 days)",
                "severity": "medium", 
                "days_violation": days_diff - 60,
                "earliest_start_date": sub.earliest_start_date, 
                "scheduled_date": interval.start_date
            })
        else:
            compliant_submissions += 1
    
    return {
        "is_valid": len(violations) == 0, 
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions within preferred timing constraints",
        "total_submissions": total_submissions, 
        "compliant_submissions": compliant_submissions
    }


def _calculate_daily_load(schedule: Schedule, config: Config) -> Dict[date, int]:
    """Calculate daily resource load from schedule."""
    daily_load = {}
    
    for sid, interval in schedule.intervals.items():
        submission = config.submissions_dict.get(sid)
        if not submission:
            continue
        
        duration = submission.get_duration_days(config)
        for i in range(duration):
            check_date = interval.start_date + timedelta(days=i)
            daily_load[check_date] = daily_load.get(check_date, 0) + 1
    
    return daily_load


def _validate_peak_load(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate peak load constraints."""
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return {"is_valid": True, "peak_load": 0, "max_allowed": config.max_concurrent_submissions}
    
    peak_load = max(daily_load.values())
    is_valid = peak_load <= config.max_concurrent_submissions
    
    return {
        "is_valid": is_valid,
        "peak_load": peak_load,
        "max_allowed": config.max_concurrent_submissions,
        "violations": [] if is_valid else [{"peak_load": peak_load, "max_allowed": config.max_concurrent_submissions}]
    }


def _validate_average_load(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate average load constraints."""
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return {"is_valid": True, "average_load": 0.0}
    
    total_load = sum(daily_load.values())
    average_load = total_load / len(daily_load)
    
    # Check if average load is reasonable (e.g., not too close to max)
    max_load = config.max_concurrent_submissions
    threshold = max_load * 0.8  # 80% of max capacity
    
    is_valid = average_load <= threshold
    
    return {
        "is_valid": is_valid,
        "average_load": average_load,
        "threshold": threshold,
        "max_capacity": max_load
    }
