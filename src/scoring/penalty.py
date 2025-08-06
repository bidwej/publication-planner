"""Calculate penalty scores for schedule violations."""

from __future__ import annotations
from typing import Dict
from datetime import date, timedelta
from core.models import Config, Submission, SubmissionType, PenaltyBreakdown

def calculate_penalty_score(schedule: Dict[str, date], config: Config) -> PenaltyBreakdown:
    """Calculate total penalty score for the schedule."""
    if not schedule:
        return PenaltyBreakdown(
            total_penalty=0.0,
            deadline_penalties=0.0,
            dependency_penalties=0.0,
            resource_penalties=0.0
        )
    
    deadline_penalties = _calculate_deadline_penalties(schedule, config)
    dependency_penalties = _calculate_dependency_penalties(schedule, config)
    resource_penalties = _calculate_resource_penalties(schedule, config)
    
    total_penalty = deadline_penalties + dependency_penalties + resource_penalties
    
    return PenaltyBreakdown(
        total_penalty=total_penalty,
        deadline_penalties=deadline_penalties,
        dependency_penalties=dependency_penalties,
        resource_penalties=resource_penalties
    )

def _calculate_deadline_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for missed deadlines."""
    total_penalty = 0.0
    
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
        
        # Calculate penalty if deadline is missed
        if end_date > deadline:
            days_late = (end_date - deadline).days
            penalty_per_day = sub.penalty_cost_per_day or (config.penalty_costs or {}).get("default_penalty_per_day", 100.0)
            total_penalty += days_late * penalty_per_day
    
    return total_penalty

def _calculate_dependency_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for dependency violations."""
    total_penalty = 0.0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        for dep_id in sub.depends_on:
            if dep_id not in schedule:
                # Missing dependency - high penalty
                total_penalty += 1000.0
                continue
            
            dep_start = schedule[dep_id]
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                continue
            
            # Calculate dependency end date
            if dep_sub.kind == SubmissionType.PAPER:
                dep_duration = config.min_paper_lead_time_days
            else:
                dep_duration = 0
            
            dep_end = dep_start + timedelta(days=dep_duration)
            
            # Check if dependency is satisfied
            if dep_end > start_date:
                days_violation = (dep_end - start_date).days
                total_penalty += days_violation * 50.0
    
    return total_penalty

def _calculate_resource_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for resource constraint violations."""
    total_penalty = 0.0
    daily_load = {}
    max_concurrent = config.max_concurrent_submissions
    
    # Calculate daily workload
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    # Calculate penalties for violations
    for day, load in daily_load.items():
        if load > max_concurrent:
            excess = load - max_concurrent
            penalty_per_excess = (config.penalty_costs or {}).get("resource_violation_penalty", 200.0)
            total_penalty += excess * penalty_per_excess
    
    return total_penalty

 