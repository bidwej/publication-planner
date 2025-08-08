"""Resource validation functions for concurrency constraints."""

from typing import Dict, Any
from datetime import date, timedelta

from src.core.models import Config, ResourceValidation, ResourceViolation
from src.core.constants import QUALITY_CONSTANTS


def validate_resources_all_constraints(schedule: Dict[str, date], config: Config) -> ResourceValidation:
    """Validate all resource-related constraints for the complete schedule."""
    return _validate_resource_constraints(schedule, config)


def _validate_resource_constraints(schedule: Dict[str, date], config: Config) -> ResourceValidation:
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
    
    if not daily_load:
        return ResourceValidation(
            is_valid=True,
            violations=[],
            summary="No active submissions",
            max_concurrent=max_concurrent,
            max_observed=0,
            total_days=0
        )
    
    # Find violations
    max_observed = 0
    total_days = len(daily_load)
    
    for day, count in daily_load.items():
        max_observed = max(max_observed, count)
        
        if count > max_concurrent:
            violations.append(ResourceViolation(
                submission_id="",  # Multiple submissions could be involved
                description=f"Too many concurrent submissions on {day}: {count} > {max_concurrent}",
                severity="high",
                date=day,
                load=count,
                limit=max_concurrent,
                excess=count - max_concurrent
            ))
    
    is_valid = len(violations) == 0
    
    return ResourceValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"Resource constraints: max {max_observed} concurrent (limit: {max_concurrent})",
        max_concurrent=max_concurrent,
        max_observed=max_observed,
        total_days=total_days
    )


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
    
    for submission_id, start_date in schedule.items():
        submission = config.submissions_dict.get(submission_id)
        if not submission:
            continue
            
        duration_days = submission.get_duration_days(config)
        for i in range(duration_days):
            current_date = start_date + timedelta(days=i)
            daily_load[current_date] = daily_load.get(current_date, 0) + 1
    
    return daily_load
