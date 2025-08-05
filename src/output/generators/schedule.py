"""Schedule-specific output generation."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date, datetime
from ...models import Config, Submission
from ...scoring.penalty import calculate_penalty_score
from ...scoring.quality import calculate_quality_score
from ...scoring.efficiency import calculate_efficiency_score
from ...constraints import validate_deadline_compliance, validate_resource_constraints

def generate_schedule_summary(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Generate a comprehensive schedule summary."""
    if not schedule:
        return {
            "total_submissions": 0,
            "schedule_span": 0,
            "start_date": None,
            "end_date": None,
            "penalty_score": 0.0,
            "quality_score": 0.0,
            "efficiency_score": 0.0,
            "deadline_compliance": 100.0,
            "resource_utilization": 0.0
        }
    
    # Basic schedule metrics
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    schedule_span = (end_date - start_date).days
    
    # Calculate scores
    penalty = calculate_penalty_score(schedule, config)
    quality = calculate_quality_score(schedule, config)
    efficiency = calculate_efficiency_score(schedule, config)
    
    # Calculate compliance
    deadline_validation = validate_deadline_compliance(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    return {
        "total_submissions": len(schedule),
        "schedule_span": schedule_span,
        "start_date": start_date,
        "end_date": end_date,
        "penalty_score": penalty.total_penalty,
        "quality_score": quality,
        "efficiency_score": efficiency,
        "deadline_compliance": deadline_validation.compliance_rate,
        "resource_utilization": resource_validation.max_observed / resource_validation.max_concurrent if resource_validation.max_concurrent > 0 else 0.0
    }

def generate_schedule_metrics(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Generate detailed metrics for the schedule."""
    if not schedule:
        return {
            "makespan": 0,
            "avg_utilization": 0.0,
            "peak_utilization": 0,
            "total_penalty": 0.0,
            "compliance_rate": 100.0,
            "quality_score": 0.0
        }
    
    # Calculate makespan
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    makespan = (end_date - start_date).days
    
    # Calculate utilization
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Calculate duration
        if sub.kind.value == "ABSTRACT":
            duration_days = 0
        else:
            duration_days = sub.draft_window_months * 30 if sub.draft_window_months > 0 else config.min_paper_lead_time_days
        
        # Add workload for each day
        for i in range(duration_days + 1):
            day = start_date + datetime.timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    avg_utilization = sum(daily_load.values()) / len(daily_load) if daily_load else 0.0
    peak_utilization = max(daily_load.values()) if daily_load else 0
    
    # Calculate penalties and compliance
    penalty = calculate_penalty_score(schedule, config)
    deadline_validation = validate_deadline_compliance(schedule, config)
    quality = calculate_quality_score(schedule, config)
    
    return {
        "makespan": makespan,
        "avg_utilization": avg_utilization,
        "peak_utilization": peak_utilization,
        "total_penalty": penalty.total_penalty,
        "compliance_rate": deadline_validation.compliance_rate,
        "quality_score": quality
    } 