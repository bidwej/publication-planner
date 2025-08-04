"""Analytics functions for schedule insights and reporting."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType, ScheduleAnalysis, ScheduleDistribution, SubmissionTypeAnalysis

def analyze_schedule_completeness(schedule: Dict[str, date], config: Config) -> ScheduleAnalysis:
    """Analyze how complete the schedule is."""
    if not schedule:
        return ScheduleAnalysis(
            scheduled_count=0,
            total_count=0,
            completion_rate=0.0,
            missing_submissions=[]
        )
    
    total_submissions = len(config.submissions)
    scheduled_count = len(schedule)
    completion_rate = (scheduled_count / total_submissions * 100) if total_submissions > 0 else 0.0
    
    # Find missing submissions
    scheduled_ids = set(schedule.keys())
    all_ids = {sub.id for sub in config.submissions}
    missing_ids = all_ids - scheduled_ids
    
    missing_submissions = [
        {
            "id": sub.id,
            "title": sub.title,
            "kind": sub.kind.value,
            "conference_id": sub.conference_id
        }
        for sub in config.submissions
        if sub.id in missing_ids
    ]
    
    return ScheduleAnalysis(
        scheduled_count=scheduled_count,
        total_count=total_submissions,
        completion_rate=completion_rate,
        missing_submissions=missing_submissions
    )

def analyze_schedule_distribution(schedule: Dict[str, date], config: Config) -> ScheduleDistribution:
    """Analyze the distribution of submissions across time."""
    if not schedule:
        return ScheduleDistribution(
            monthly_distribution={},
            quarterly_distribution={},
            yearly_distribution={}
        )
    
    # Monthly distribution
    monthly_dist = {}
    for sid, start_date in schedule.items():
        month_key = f"{start_date.year}-{start_date.month:02d}"
        monthly_dist[month_key] = monthly_dist.get(month_key, 0) + 1
    
    # Quarterly distribution
    quarterly_dist = {}
    for sid, start_date in schedule.items():
        quarter = (start_date.month - 1) // 3 + 1
        quarter_key = f"{start_date.year}-Q{quarter}"
        quarterly_dist[quarter_key] = quarterly_dist.get(quarter_key, 0) + 1
    
    # Yearly distribution
    yearly_dist = {}
    for sid, start_date in schedule.items():
        year_key = str(start_date.year)
        yearly_dist[year_key] = yearly_dist.get(year_key, 0) + 1
    
    return ScheduleDistribution(
        monthly_distribution=monthly_dist,
        quarterly_distribution=quarterly_dist,
        yearly_distribution=yearly_dist
    )

def analyze_submission_types(schedule: Dict[str, date], config: Config) -> SubmissionTypeAnalysis:
    """Analyze the distribution of submission types in the schedule."""
    if not schedule:
        return SubmissionTypeAnalysis(
            type_counts={},
            type_percentages={}
        )
    
    type_counts = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        sub_type = sub.kind.value
        type_counts[sub_type] = type_counts.get(sub_type, 0) + 1
    
    # Calculate percentages
    total_scheduled = len(schedule)
    type_percentages = {
        sub_type: (count / total_scheduled * 100) if total_scheduled > 0 else 0.0
        for sub_type, count in type_counts.items()
    }
    
    return SubmissionTypeAnalysis(
        type_counts=type_counts,
        type_percentages=type_percentages
    )

def analyze_timeline(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Analyze timeline characteristics of the schedule."""
    if not schedule:
        return {
            "start_date": None,
            "end_date": None,
            "duration_days": 0,
            "avg_submissions_per_month": 0.0
        }
    
    dates = list(schedule.values())
    start_date = min(dates)
    end_date = max(dates)
    duration_days = (end_date - start_date).days
    
    # Calculate average submissions per month
    months_span = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    avg_per_month = len(schedule) / months_span if months_span > 0 else 0.0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration_days,
        "avg_submissions_per_month": avg_per_month
    }

def analyze_resources(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Analyze resource utilization patterns."""
    if not schedule:
        return {
            "peak_load": 0,
            "avg_load": 0.0,
            "utilization_pattern": {}
        }
    
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
    
    if not daily_load:
        return {
            "peak_load": 0,
            "avg_load": 0.0,
            "utilization_pattern": {}
        }
    
    peak_load = max(daily_load.values())
    avg_load = sum(daily_load.values()) / len(daily_load)
    
    return {
        "peak_load": peak_load,
        "avg_load": avg_load,
        "utilization_pattern": daily_load
    } 