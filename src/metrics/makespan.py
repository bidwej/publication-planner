from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType

def calculate_makespan(schedule: Dict[str, date], config: Config) -> int:
    """Calculate the total makespan of a schedule in days."""
    if not schedule:
        return 0
    
    end_dates = []
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        end_dates.append(end_date)
    
    if not end_dates:
        return 0
    
    makespan = max(end_dates) - min(schedule.values())
    return makespan.days

def calculate_parallel_makespan(schedule: Dict[str, date], config: Config) -> int:
    """Calculate the parallel makespan considering resource constraints."""
    if not schedule:
        return 0
    
    # Group submissions by start date
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
        return 0
    
    # Find the maximum daily load
    max_load = max(daily_load.values())
    
    # Calculate parallel makespan based on resource constraints
    total_work = len([s for s in config.submissions_dict.values() if s.kind == SubmissionType.PAPER])
    parallel_makespan = total_work / max_load if max_load > 0 else 0
    
    return int(parallel_makespan)

def get_makespan_breakdown(schedule: Dict[str, date], config: Config) -> Dict[str, int]:
    """Get detailed makespan breakdown by submission type."""
    breakdown = {
        "abstracts": 0,
        "papers": 0,
        "total": 0
    }
    
    if not schedule:
        return breakdown
    
    abstract_end_dates = []
    paper_end_dates = []
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.ABSTRACT:
            end_date = start_date
            abstract_end_dates.append(end_date)
        else:
            duration = config.min_paper_lead_time_days
            end_date = start_date + timedelta(days=duration)
            paper_end_dates.append(end_date)
    
    if abstract_end_dates:
        breakdown["abstracts"] = (max(abstract_end_dates) - min(abstract_end_dates)).days
    
    if paper_end_dates:
        breakdown["papers"] = (max(paper_end_dates) - min(paper_end_dates)).days
    
    breakdown["total"] = calculate_makespan(schedule, config)
    
    return breakdown


def get_schedule_metrics(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate comprehensive metrics for a given schedule."""
    if not schedule:
        return {}
    
    # Calculate makespan
    makespan = calculate_makespan(schedule, config)
    
    # Calculate average start date (as days from epoch)
    start_dates = list(schedule.values())
    avg_start_date = sum(d.toordinal() for d in start_dates) / len(start_dates) if start_dates else 0
    
    return {
        "makespan_days": makespan,
        "total_submissions": len(schedule),
        "avg_start_date": avg_start_date
    } 