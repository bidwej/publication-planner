from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType

def calculate_penalty_costs(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate penalty costs for missed deadlines and other violations."""
    if not schedule:
        return {"total_penalty": 0.0, "deadline_penalties": 0.0, "dependency_penalties": 0.0}
    
    total_penalty = 0.0
    deadline_penalties = 0.0
    dependency_penalties = 0.0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Calculate deadline penalty
        deadline_penalty = calculate_deadline_penalty(sub, start_date, config)
        deadline_penalties += deadline_penalty
        
        # Calculate dependency penalty
        dependency_penalty = calculate_dependency_penalty(sub, schedule, config)
        dependency_penalties += dependency_penalty
        
        total_penalty += deadline_penalty + dependency_penalty
    
    return {
        "total_penalty": total_penalty,
        "deadline_penalties": deadline_penalties,
        "dependency_penalties": dependency_penalties
    }

def calculate_deadline_penalty(sub: Submission, start_date: date, config: Config) -> float:
    """Calculate penalty for missing deadline."""
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return 0.0
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return 0.0
    
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
        penalty_per_day = sub.penalty_cost_per_day or config.penalty_costs.get("default_penalty_per_day", 100.0)
        return days_late * penalty_per_day
    
    return 0.0

def calculate_dependency_penalty(sub: Submission, schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalty for dependency violations."""
    penalty = 0.0
    
    for dep_id in sub.depends_on:
        if dep_id not in schedule:
            # Missing dependency - high penalty
            penalty += 1000.0
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
        if dep_end > schedule.get(sub.id, date.max):
            # Dependency not satisfied - penalty
            days_violation = (dep_end - schedule.get(sub.id, date.max)).days
            penalty += days_violation * 50.0
    
    return penalty

def calculate_earliness_bonus(schedule: Dict[str, date], config: Config) -> float:
    """Calculate bonus for completing submissions early."""
    if not schedule:
        return 0.0
    
    total_bonus = 0.0
    
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
        
        # Calculate bonus for early completion
        if end_date < deadline:
            days_early = (deadline - end_date).days
            bonus_per_day = config.penalty_costs.get("early_completion_bonus_per_day", 10.0)
            total_bonus += days_early * bonus_per_day
    
    return total_bonus

def get_penalty_breakdown(schedule: Dict[str, date], config: Config) -> Dict[str, Dict]:
    """Get detailed penalty breakdown by submission."""
    breakdown = {}
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        deadline_penalty = calculate_deadline_penalty(sub, start_date, config)
        dependency_penalty = calculate_dependency_penalty(sub, schedule, config)
        
        breakdown[sid] = {
            "deadline_penalty": deadline_penalty,
            "dependency_penalty": dependency_penalty,
            "total_penalty": deadline_penalty + dependency_penalty
        }
    
    return breakdown 