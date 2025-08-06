"""Quality scoring functions."""

from typing import Dict, List
from datetime import date, timedelta
from collections import defaultdict

from core.models import Config, SubmissionType
from core.constraints import validate_deadline_compliance, validate_dependency_satisfaction, validate_resource_constraints
from core.constants import (
    MAX_SCORE, MIN_SCORE, ROBUSTNESS_SCALE_FACTOR, BALANCE_VARIANCE_FACTOR,
    SINGLE_SUBMISSION_ROBUSTNESS, SINGLE_SUBMISSION_BALANCE
)

def calculate_quality_score(schedule: Dict[str, date], config: Config) -> float:
    """Calculate overall quality score (0-100) based on constraint compliance."""
    if not schedule:
        return MIN_SCORE
    
    # Get constraint validations (quality is based on how well constraints are satisfied)
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    # Calculate component scores from constraint compliance
    deadline_score = deadline_validation.compliance_rate
    dependency_score = dependency_validation.satisfaction_rate
    resource_score = MAX_SCORE if resource_validation.is_valid else 50.0
    
    # Weighted average based on constraint importance
    weights = {
        "deadline": 0.4,      # Deadlines are most important
        "dependency": 0.3,    # Dependencies are important
        "resource": 0.3       # Resource constraints are important
    }
    
    quality_score = (
        deadline_score * weights["deadline"] +
        dependency_score * weights["dependency"] +
        resource_score * weights["resource"]
    )
    
    return min(MAX_SCORE, max(MIN_SCORE, quality_score))

def calculate_quality_robustness(schedule: Dict[str, date], config: Config) -> float:
    """Calculate how robust the schedule is to disruptions."""
    if not schedule:
        return MIN_SCORE
    
    # Calculate slack time (buffer between submissions)
    total_slack = 0
    total_submissions = len(schedule)
    
    if total_submissions < 2:
        return SINGLE_SUBMISSION_ROBUSTNESS  # Single submission is always robust
    
    # Sort submissions by start date
    sorted_submissions = sorted(schedule.items(), key=lambda x: x[1])
    
    for i in range(len(sorted_submissions) - 1):
        current_id, current_start = sorted_submissions[i]
        next_id, next_start = sorted_submissions[i + 1]
        
        current_sub = config.submissions_dict.get(current_id)
        if not current_sub:
            continue
        
        # Calculate current submission end date
        if current_sub.kind == SubmissionType.PAPER:
            current_duration = config.min_paper_lead_time_days
        else:
            current_duration = 0
        
        current_end = current_start + timedelta(days=current_duration)
        
        # Calculate slack between current and next submission
        slack_days = (next_start - current_end).days
        if slack_days > 0:
            total_slack += slack_days
    
    # Robustness score based on average slack
    avg_slack = total_slack / (total_submissions - 1) if total_submissions > 1 else 0
    robustness_score = min(MAX_SCORE, avg_slack * ROBUSTNESS_SCALE_FACTOR)  # Scale slack to 0-100
    
    return max(MIN_SCORE, robustness_score)

def calculate_quality_balance(schedule: Dict[str, date], config: Config) -> float:
    """Calculate how well balanced the schedule is."""
    if not schedule:
        return MIN_SCORE
    
    # Calculate work distribution over time
    daily_work = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add work for each day
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_work[day] = daily_work.get(day, 0) + 1
    
    if not daily_work:
        return MIN_SCORE
    
    # Calculate balance score based on work distribution
    work_values = list(daily_work.values())
    avg_work = sum(work_values) / len(work_values)
    max_work = max(work_values)
    
    # Balance score (lower variance is better)
    if avg_work == 0:
        return SINGLE_SUBMISSION_BALANCE
    
    variance = sum((w - avg_work) ** 2 for w in work_values) / len(work_values)
    balance_score = max(MIN_SCORE, MAX_SCORE - (variance / avg_work) * BALANCE_VARIANCE_FACTOR)
    
    return min(MAX_SCORE, balance_score) 