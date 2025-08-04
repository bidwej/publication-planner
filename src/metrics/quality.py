from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType
from .deadlines import calculate_deadline_compliance
from .utilization import calculate_resource_utilization
from .penalties import calculate_penalty_costs

def calculate_schedule_quality_score(schedule: Dict[str, date], config: Config) -> float:
    """Calculate overall quality score for a schedule."""
    if not schedule:
        return 0.0
    
    # Calculate individual quality metrics
    deadline_compliance = calculate_deadline_compliance(schedule, config)
    utilization = calculate_resource_utilization(schedule, config)
    penalties = calculate_penalty_costs(schedule, config)
    
    # Weighted quality score
    compliance_weight = 0.4
    utilization_weight = 0.3
    penalty_weight = 0.3
    
    # Normalize penalty (lower is better, so invert)
    max_penalty = 10000.0  # Reasonable maximum penalty
    normalized_penalty = max(0, 1 - (penalties["total_penalty"] / max_penalty))
    
    quality_score = (
        (deadline_compliance["compliance_rate"] / 100) * compliance_weight +
        utilization["avg_utilization"] * utilization_weight +
        normalized_penalty * penalty_weight
    )
    
    return quality_score

def calculate_front_loading_score(schedule: Dict[str, date], config: Config) -> float:
    """Calculate how well the schedule front-loads work."""
    if not schedule:
        return 0.0
    
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
        return 0.0
    
    # Calculate front-loading score
    sorted_dates = sorted(daily_work.keys())
    total_days = len(sorted_dates)
    
    if total_days == 0:
        return 0.0
    
    # Calculate work in first half vs second half
    mid_point = total_days // 2
    first_half_work = sum(daily_work[day] for day in sorted_dates[:mid_point])
    second_half_work = sum(daily_work[day] for day in sorted_dates[mid_point:])
    
    total_work = first_half_work + second_half_work
    if total_work == 0:
        return 0.0
    
    front_loading_ratio = first_half_work / total_work
    return front_loading_ratio

def calculate_slack_distribution(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate slack time distribution in the schedule."""
    if not schedule:
        return {"avg_slack_days": 0.0, "min_slack_days": 0.0, "max_slack_days": 0.0}
    
    slacks = []
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        # Calculate slack (positive if early, negative if late)
        slack = (deadline - end_date).days
        slacks.append(slack)
    
    if not slacks:
        return {"avg_slack_days": 0.0, "min_slack_days": 0.0, "max_slack_days": 0.0}
    
    return {
        "avg_slack_days": sum(slacks) / len(slacks),
        "min_slack_days": min(slacks),
        "max_slack_days": max(slacks)
    }

def calculate_workload_balance(schedule: Dict[str, date], config: Config) -> float:
    """Calculate how well the workload is balanced over time."""
    if not schedule:
        return 0.0
    
    # Calculate daily workload
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
        return 0.0
    
    # Calculate coefficient of variation (lower is more balanced)
    workloads = list(daily_work.values())
    mean_workload = sum(workloads) / len(workloads)
    
    if mean_workload == 0:
        return 1.0  # Perfect balance if no work
    
    variance = sum((w - mean_workload) ** 2 for w in workloads) / len(workloads)
    std_dev = variance ** 0.5
    coefficient_of_variation = std_dev / mean_workload
    
    # Convert to balance score (1.0 = perfectly balanced, 0.0 = very unbalanced)
    balance_score = max(0, 1 - coefficient_of_variation)
    return balance_score

def calculate_dependency_satisfaction(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate how well dependencies are satisfied."""
    if not schedule:
        return {"satisfaction_rate": 0.0, "total_dependencies": 0, "satisfied_dependencies": 0}
    
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        for dep_id in sub.depends_on:
            total_dependencies += 1
            
            if dep_id not in schedule:
                continue
            
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                continue
            
            dep_start = schedule[dep_id]
            
            # Calculate dependency end date
            if dep_sub.kind == SubmissionType.PAPER:
                dep_duration = config.min_paper_lead_time_days
            else:
                dep_duration = 0
            
            dep_end = dep_start + timedelta(days=dep_duration)
            
            # Check if dependency is satisfied
            if dep_end <= start_date:
                satisfied_dependencies += 1
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * 100) if total_dependencies > 0 else 0.0
    
    return {
        "satisfaction_rate": satisfaction_rate,
        "total_dependencies": total_dependencies,
        "satisfied_dependencies": satisfied_dependencies
    } 