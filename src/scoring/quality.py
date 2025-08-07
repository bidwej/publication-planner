"""Quality scoring functions."""

from typing import Dict, Any
from datetime import date, timedelta
import statistics

from core.models import Config
from core.constraints import validate_deadline_compliance, validate_dependency_satisfaction, validate_resource_constraints
from core.constants import (
    QUALITY_CONSTANTS, SCORING_CONSTANTS, REPORT_CONSTANTS
)

def calculate_quality_score(schedule: Dict[str, date], config: Config) -> float:
    """Calculate overall quality score (0-100) based on constraint compliance."""
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    # Get constraint validations
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    # Calculate component scores
    deadline_score = deadline_validation.compliance_rate
    dependency_score = dependency_validation.satisfaction_rate
    resource_score = max_score if resource_validation.is_valid else QUALITY_CONSTANTS.quality_resource_fallback_score
    
    # Calculate weighted score
    quality_score = (
        deadline_score * SCORING_CONSTANTS.quality_deadline_weight +
        dependency_score * SCORING_CONSTANTS.quality_dependency_weight +
        resource_score * SCORING_CONSTANTS.quality_resource_weight
    )
    
    return min(max_score, max(min_score, quality_score))

def calculate_quality_robustness(schedule: Dict[str, date], config: Config) -> float:
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


def _calculate_total_slack(schedule: Dict[str, date], config: Config) -> int:
    """Calculate total slack time between submissions."""
    sorted_submissions = sorted(schedule.items(), key=lambda x: x[1])
    total_slack = 0
    
    for i in range(len(sorted_submissions) - 1):
        current_id, current_start = sorted_submissions[i]
        next_id, next_start = sorted_submissions[i + 1]
        
        current_sub = config.submissions_dict.get(current_id)
        if not current_sub:
            continue
        
        current_duration = current_sub.get_duration_days(config)
        current_end = current_start + timedelta(days=current_duration)
        slack_days = (next_start - current_end).days
        
        if slack_days > 0:
            total_slack += slack_days
    
    return total_slack

def calculate_quality_balance(schedule: Dict[str, date], config: Config) -> float:
    """Calculate how well balanced the schedule is."""
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    # Calculate work distribution over time
    daily_work = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Use proper duration calculation for all submission types
        duration = sub.get_duration_days(config)
        
        # Add work for each day
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
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