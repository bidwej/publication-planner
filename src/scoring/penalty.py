"""Penalty scoring functions."""

from typing import Dict
from datetime import date, timedelta
from collections import defaultdict

from core.models import Config, PenaltyBreakdown, SubmissionType, ConferenceType
from core.constants import (
    MIN_SCORE, TECHNICAL_AUDIENCE_LOSS_PENALTY, AUDIENCE_MISMATCH_PENALTY,
    DEFAULT_DEPENDENCY_VIOLATION_PENALTY
)
# Note: Penalty costs moved to config.json because they are project-specific
# and should be configurable by users. Only algorithm constants remain in constants.py.

def calculate_penalty_score(schedule: Dict[str, date], config: Config) -> PenaltyBreakdown:
    """Calculate total penalty score for the schedule."""
    if not schedule:
        return PenaltyBreakdown(
            total_penalty=MIN_SCORE,
            deadline_penalties=MIN_SCORE,
            dependency_penalties=MIN_SCORE,
            resource_penalties=MIN_SCORE
        )
    
    deadline_penalties = _calculate_deadline_penalties(schedule, config)
    dependency_penalties = _calculate_dependency_penalties(schedule, config)
    resource_penalties = _calculate_resource_penalties(schedule, config)
    conference_penalties = _calculate_conference_compatibility_penalties(schedule, config)
    slack_penalties = _calculate_slack_cost_penalties(schedule, config)
    
    total_penalty = deadline_penalties + dependency_penalties + resource_penalties + conference_penalties + slack_penalties
    
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
            # Use config penalty costs (project-specific) instead of constants
            penalty_per_day = sub.penalty_cost_per_day or (config.penalty_costs or {}).get("default_mod_penalty_per_day", 1000.0)
            total_penalty += days_late * penalty_per_day
    
    return total_penalty

def _calculate_dependency_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for dependency violations."""
    total_penalty = 0.0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        for dep_id in (sub.depends_on or []):
            if dep_id not in schedule:
                # Missing dependency - use config penalty (project-specific)
                monthly_penalty = (config.penalty_costs or {}).get("default_monthly_slip_penalty", 1000.0)
                total_penalty += monthly_penalty
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
            if start_date < dep_end:
                # Dependency violation - use config penalty (project-specific)
                penalty = (config.penalty_costs or {}).get("default_dependency_violation_penalty", DEFAULT_DEPENDENCY_VIOLATION_PENALTY)
                total_penalty += penalty
    
    return total_penalty

def _calculate_resource_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for resource constraint violations."""
    total_penalty = 0.0
    
    # Calculate daily load
    daily_load = defaultdict(int)
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Calculate duration
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day
        for i in range(duration):
            check_date = start_date + timedelta(days=i)
            daily_load[check_date] += 1
    
    # Check against max concurrent submissions
    max_concurrent = config.max_concurrent_submissions
    for load in daily_load.values():
        if load > max_concurrent:
            excess = load - max_concurrent
            # Use config penalty costs (project-specific) instead of constants
            penalty_per_excess = (config.penalty_costs or {}).get("resource_violation_penalty", 200.0)
            total_penalty += excess * penalty_per_excess
    
    return total_penalty

def _calculate_conference_compatibility_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for conference compatibility issues."""
    total_penalty = 0.0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        
        # Check engineering vs medical mismatch
        if sub.engineering and conf.conf_type == ConferenceType.MEDICAL:
            total_penalty += TECHNICAL_AUDIENCE_LOSS_PENALTY
        elif not sub.engineering and conf.conf_type == ConferenceType.ENGINEERING:
            total_penalty += AUDIENCE_MISMATCH_PENALTY
    
    return total_penalty

def _calculate_slack_cost_penalties(schedule: Dict[str, date], config: Config) -> float:
    """Calculate penalties for slack costs (opportunity costs)."""
    total_penalty = 0.0
    
    # Calculate P_j (monthly slip penalty)
    P_j = (config.penalty_costs or {}).get("default_monthly_slip_penalty", 1000.0)
    
    # Calculate Y_j (full-year deferral penalty)
    Y_j = (config.penalty_costs or {}).get("default_full_year_deferral_penalty", 5000.0)
    
    A_j = (config.penalty_costs or {}).get("missed_abstract_penalty", 3000.0)  # Missed abstract-only window penalty
    
    # Calculate slack cost components for each submission
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        if sub.earliest_start_date:
            # P_j(S_j - S_j,earliest) - monthly slip penalty
            months_delay = max(0, (start_date.year - sub.earliest_start_date.year) * 12 + 
                             (start_date.month - sub.earliest_start_date.month))
            slip_penalty = P_j * months_delay
            
            # Y_j(1_year-deferred) - full-year deferral penalty
            if months_delay >= 12:
                deferral_penalty = Y_j
            else:
                deferral_penalty = 0
            
            # A_j(1_abstract-miss) - missed abstract penalty
            # This would need more complex logic to determine if abstract was missed
            abstract_penalty = 0  # Placeholder for now
            
            total_penalty += slip_penalty + deferral_penalty + abstract_penalty
    
    return total_penalty

 