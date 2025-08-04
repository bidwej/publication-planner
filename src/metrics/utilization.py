from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType

def calculate_resource_utilization(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate resource utilization metrics."""
    if not schedule:
        return {"avg_utilization": 0.0, "max_utilization": 0.0, "min_utilization": 0.0}
    
    # Calculate daily resource usage
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day of the submission
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    if not daily_load:
        return {"avg_utilization": 0.0, "max_utilization": 0.0, "min_utilization": 0.0}
    
    # Calculate utilization relative to max concurrent submissions
    max_concurrent = config.max_concurrent_submissions
    utilizations = [load / max_concurrent for load in daily_load.values()]
    
    return {
        "avg_utilization": sum(utilizations) / len(utilizations),
        "max_utilization": max(utilizations),
        "min_utilization": min(utilizations)
    }

def calculate_peak_utilization_periods(schedule: Dict[str, date], config: Config, threshold: float = 0.8) -> List[Dict]:
    """Find periods of high resource utilization."""
    if not schedule:
        return []
    
    # Calculate daily resource usage
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day of the submission
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    # Find peak periods
    peak_periods = []
    max_concurrent = config.max_concurrent_submissions
    
    sorted_dates = sorted(daily_load.keys())
    current_period_start = None
    
    for day in sorted_dates:
        utilization = daily_load[day] / max_concurrent
        
        if utilization >= threshold:
            if current_period_start is None:
                current_period_start = day
        else:
            if current_period_start is not None:
                peak_periods.append({
                    "start": current_period_start,
                    "end": day - timedelta(days=1),
                    "avg_utilization": sum(daily_load[d] / max_concurrent 
                                         for d in range((day - current_period_start).days)) / (day - current_period_start).days
                })
                current_period_start = None
    
    # Handle case where period extends to the end
    if current_period_start is not None:
        peak_periods.append({
            "start": current_period_start,
            "end": sorted_dates[-1],
            "avg_utilization": sum(daily_load[d] / max_concurrent 
                                 for d in range((sorted_dates[-1] - current_period_start + timedelta(days=1)).days)) / (sorted_dates[-1] - current_period_start + timedelta(days=1)).days
        })
    
    return peak_periods

def calculate_idle_periods(schedule: Dict[str, date], config: Config) -> List[Dict]:
    """Find periods of low resource utilization (idle time)."""
    if not schedule:
        return []
    
    # Calculate daily resource usage
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day of the submission
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    # Find idle periods (utilization < 0.5)
    idle_periods = []
    max_concurrent = config.max_concurrent_submissions
    
    sorted_dates = sorted(daily_load.keys())
    current_period_start = None
    
    for day in sorted_dates:
        utilization = daily_load[day] / max_concurrent
        
        if utilization < 0.5:
            if current_period_start is None:
                current_period_start = day
        else:
            if current_period_start is not None:
                idle_periods.append({
                    "start": current_period_start,
                    "end": day - timedelta(days=1),
                    "avg_utilization": sum(daily_load[d] / max_concurrent 
                                         for d in range((day - current_period_start).days)) / (day - current_period_start).days
                })
                current_period_start = None
    
    # Handle case where period extends to the end
    if current_period_start is not None:
        idle_periods.append({
            "start": current_period_start,
            "end": sorted_dates[-1],
            "avg_utilization": sum(daily_load[d] / max_concurrent 
                                 for d in range((sorted_dates[-1] - current_period_start + timedelta(days=1)).days)) / (sorted_dates[-1] - current_period_start + timedelta(days=1)).days
        })
    
    return idle_periods 