"""Quality scoring functions."""

from typing import Dict, Any
from datetime import date, timedelta
import statistics

from core.models import Config, Schedule
from validation.deadline import validate_deadline_constraints
from validation.schedule import validate_schedule_constraints
from validation.resources import validate_resources_constraints
from core.constants import (
    QUALITY_CONSTANTS, SCORING_CONSTANTS, REPORT_CONSTANTS
)

def calculate_quality_score(schedule: Schedule, config: Config) -> float:
    """
    Calculate quality score based on deadline compliance, dependencies, and resource utilization.
    
    Parameters
    ----------
    schedule : Schedule
        Schedule object with intervals
    config : Config
        Configuration object
        
    Returns
    -------
    float
        Quality score (0-100)
    """
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    # Get comprehensive constraint validations
    comprehensive_result = validate_schedule_constraints(schedule, config)
    
    # Extract constraint results from the ValidationResult object
    # The comprehensive_result is a ValidationResult, not a dict
    deadline_score = max_score
    dependency_score = max_score
    resource_score = max_score
    
    # Check if there are violations to calculate scores
    if comprehensive_result.violations:
        total_violations = len(comprehensive_result.violations)
        deadline_violations = len([v for v in comprehensive_result.violations if hasattr(v, 'deadline')])
        dependency_violations = len([v for v in comprehensive_result.violations if hasattr(v, 'dependency_id')])
        resource_violations = len([v for v in comprehensive_result.violations if hasattr(v, 'load')])
        
        total_submissions = comprehensive_result.metadata.get("total_submissions", 1)
        if total_submissions > 0:
            # Calculate compliance rates based on violations
            deadline_score = max(min_score, max_score - (deadline_violations / total_submissions * max_score))
            dependency_score = max(min_score, max_score - (dependency_violations / total_submissions * max_score))
            resource_score = max(min_score, max_score - (resource_violations / total_submissions * max_score))
    
    # Additional quality factors from comprehensive validation
    additional_quality_factors = []
    
    # Check metadata for additional quality metrics
    metadata = comprehensive_result.metadata
    
    # Blackout dates compliance
    if "blackout_compliance_rate" in metadata:
        additional_quality_factors.append(metadata["blackout_compliance_rate"])
    
    # Conference compatibility
    if "compatibility_rate" in metadata:
        additional_quality_factors.append(metadata["compatibility_rate"])
    
    # Resource utilization
    if "utilization_rate" in metadata:
        additional_quality_factors.append(metadata["utilization_rate"])
    
    # Calculate weighted score with additional factors
    base_score = (
        deadline_score * SCORING_CONSTANTS.quality_deadline_weight +
        dependency_score * SCORING_CONSTANTS.quality_dependency_weight +
        resource_score * SCORING_CONSTANTS.quality_resource_weight
    )
    
    # Add additional quality factors with equal weight
    if additional_quality_factors:
        additional_score = sum(additional_quality_factors) / len(additional_quality_factors)
        # Weight the additional factors at 30% of the total score
        quality_score = base_score * SCORING_CONSTANTS.quality_deadline_weight + additional_score * SCORING_CONSTANTS.quality_dependency_weight
    else:
        quality_score = base_score
    
    # Ensure score is within bounds
    quality_score = max(min_score, min(max_score, quality_score))
    
    return quality_score

def calculate_quality_robustness(schedule: Schedule, config: Config) -> float:
    """Calculate how robust the schedule is to disruptions."""
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    total_submissions = len(schedule)
    if total_submissions < 2:
        return QUALITY_CONSTANTS.single_submission_robustness  # Single submission is always robust
    
    total_slack = _calculate_total_slack(schedule, config)
    avg_slack = total_slack / (total_submissions - 1) if total_submissions > 1 else 0
    robustness_score = min(max_score, avg_slack * QUALITY_CONSTANTS.robustness_scale_factor)
    
    return max(min_score, robustness_score)


def _calculate_total_slack(schedule: Schedule, config: Config) -> int:
    """Calculate total slack time between submissions."""
    sorted_submissions = sorted(schedule.intervals.items(), key=lambda x: x[1].start_date)
    total_slack = 0
    
    for i in range(len(sorted_submissions) - 1):
        current_id, current_interval = sorted_submissions[i]
        next_id, next_interval = sorted_submissions[i + 1]
        
        current_sub = config.get_submission(current_id)
        if not current_sub:
            continue
        
        current_duration = current_sub.get_duration_days(config)
        current_end = current_interval.start_date + timedelta(days=current_duration)
        slack_days = (next_interval.start_date - current_end).days
        
        if slack_days > 0:
            total_slack += slack_days
    
    return total_slack

def calculate_quality_balance(schedule: Schedule, config: Config) -> float:
    """Calculate how well balanced the schedule is."""
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    # Calculate work distribution over time
    daily_work = {}
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        # Use proper duration calculation for all submission types
        duration = sub.get_duration_days(config)
        
        # Add work for each day
        for i in range(duration + 1):
            day = interval.start_date + timedelta(days=i)
            daily_work[day] = daily_work.get(day, 0) + 1
    
    if not daily_work:
        return min_score
    
    # Calculate balance score based on work distribution
    work_values = list(daily_work.values())
    avg_work = statistics.mean(work_values)
    
    # Balance score (lower variance is better)
    if avg_work == 0:
        return QUALITY_CONSTANTS.single_submission_balance
    
    variance = statistics.variance(work_values)
    balance_score = max(min_score, max_score - (variance / avg_work) * QUALITY_CONSTANTS.balance_variance_factor)
    
    return min(max_score, balance_score) 
