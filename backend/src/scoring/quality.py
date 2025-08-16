"""Quality scoring functions."""

from typing import Dict, Any
from datetime import date, timedelta
import statistics

from core.models import Config
from validation.deadline import validate_deadline_constraints
from validation.schedule import validate_schedule_constraints
from validation.resources import validate_resources_constraints
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
    
    # Get comprehensive constraint validations
    from validation.schedule import validate_schedule_constraints
    comprehensive_result = validate_schedule_constraints(schedule, config)
    
    # Extract constraint results from the constraints dictionary
    constraints = comprehensive_result.get("constraints", {})
    deadline_validation = constraints.get("deadlines", {})
    dependency_validation = constraints.get("dependencies", {})
    resource_validation = constraints.get("resources", {})
    
    # Calculate component scores with comprehensive validation
    deadline_score = deadline_validation.get("compliance_rate", max_score) if isinstance(deadline_validation, dict) else max_score
    dependency_score = dependency_validation.get("satisfaction_rate", max_score) if isinstance(dependency_validation, dict) else max_score
    resource_score = max_score if resource_validation.get("is_valid", True) else QUALITY_CONSTANTS.quality_resource_fallback_score
    
    # Additional quality factors from comprehensive validation
    additional_quality_factors = []
    
    # Blackout dates compliance
    blackout_result = comprehensive_result.get("blackout_dates", {})
    if isinstance(blackout_result, dict):
        blackout_score = blackout_result.get("compliance_rate", max_score)
        additional_quality_factors.append(blackout_score)
    
    # Conference compatibility
    conf_compat_result = comprehensive_result.get("conference_compatibility", {})
    if isinstance(conf_compat_result, dict):
        conf_compat_score = conf_compat_result.get("compatibility_rate", max_score)
        additional_quality_factors.append(conf_compat_score)
    
    # Conference submission compatibility
    conf_sub_compat_result = comprehensive_result.get("conference_submission_compatibility", {})
    if isinstance(conf_sub_compat_result, dict):
        conf_sub_compat_score = conf_sub_compat_result.get("compatibility_rate", max_score)
        additional_quality_factors.append(conf_sub_compat_score)
    
    # Abstract-paper dependencies
    abstract_paper_result = comprehensive_result.get("abstract_paper_dependencies", {})
    if isinstance(abstract_paper_result, dict):
        abstract_paper_score = abstract_paper_result.get("dependency_rate", max_score)
        additional_quality_factors.append(abstract_paper_score)
    
    # Single conference policy
    single_conf_result = comprehensive_result.get("single_conference_policy", {})
    if isinstance(single_conf_result, dict):
        single_conf_score = max_score if single_conf_result.get("is_valid", True) else min_score
        additional_quality_factors.append(single_conf_score)
    
    # Soft block model
    soft_block_result = comprehensive_result.get("soft_block_model", {})
    if isinstance(soft_block_result, dict):
        soft_block_score = soft_block_result.get("compliance_rate", max_score)
        additional_quality_factors.append(soft_block_score)
    
    # Paper lead time
    lead_time_result = comprehensive_result.get("paper_lead_time", {})
    if isinstance(lead_time_result, dict):
        lead_time_score = lead_time_result.get("compliance_rate", max_score)
        additional_quality_factors.append(lead_time_score)
    
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
        quality_score = base_score * 0.7 + additional_score * 0.3
    else:
        quality_score = base_score
    
    # Ensure score is within bounds
    quality_score = max(min_score, min(max_score, quality_score))
    
    return quality_score

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
