"""Analytics functions for schedule insights and reporting."""

from __future__ import annotations
from typing import Dict
from datetime import date, timedelta
from core.models import Config, SubmissionType, ScheduleAnalysis, ScheduleDistribution, SubmissionTypeAnalysis, TimelineAnalysis, ResourceAnalysis
from core.constraints import _get_submission_duration_days, _calculate_daily_load

def analyze_schedule_completeness(schedule: Dict[str, date], config: Config) -> ScheduleAnalysis:
    """Analyze how complete the schedule is."""
    if not schedule:
        return ScheduleAnalysis(
            scheduled_count=0,
            total_count=0,
            completion_rate=0.0,
            missing_submissions=[],
            summary="No submissions to analyze"
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
        missing_submissions=missing_submissions,
        summary=f"Scheduled {scheduled_count}/{total_submissions} submissions ({completion_rate:.1f}% complete)"
    )

def analyze_schedule_distribution(schedule: Dict[str, date], config: Config) -> ScheduleDistribution:
    """Analyze the distribution of submissions across time."""
    if not schedule:
        return ScheduleDistribution(
            monthly_distribution={},
            quarterly_distribution={},
            yearly_distribution={},
            summary="No submissions to analyze"
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
        yearly_distribution=yearly_dist,
        summary=f"Distribution across {len(monthly_dist)} months, {len(quarterly_dist)} quarters, {len(yearly_dist)} years"
    )

def analyze_submission_types(schedule: Dict[str, date], config: Config) -> SubmissionTypeAnalysis:
    """Analyze the distribution of submission types in the schedule."""
    if not schedule:
        return SubmissionTypeAnalysis(
            type_counts={},
            type_percentages={},
            summary="No submissions to analyze"
        )
    
    type_counts = {}
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        sub_type = sub.kind.value
        type_counts[sub_type] = type_counts.get(sub_type, 0) + 1
    
    # Calculate percentages
    total = sum(type_counts.values())
    type_percentages = {
        sub_type: (count / total * 100) if total > 0 else 0.0
        for sub_type, count in type_counts.items()
    }
    
    return SubmissionTypeAnalysis(
        type_counts=type_counts,
        type_percentages=type_percentages,
        summary=f"Distribution across {len(type_counts)} submission types"
    )

def analyze_timeline(schedule: Dict[str, date], config: Config) -> TimelineAnalysis:
    """Analyze timeline characteristics of the schedule."""
    if not schedule:
        return TimelineAnalysis(
            start_date=None,
            end_date=None,
            duration_days=0,
            avg_submissions_per_month=0.0,
            summary="No submissions to analyze"
        )
    
    # Calculate timeline metrics
    timeline_start = min(schedule.values())
    timeline_end = max(schedule.values())
    duration_days = (timeline_end - timeline_start).days + 1
    
    # Calculate daily load using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    
    avg_daily_load = sum(daily_load.values()) / len(daily_load) if daily_load else 0.0
    peak_daily_load = max(daily_load.values()) if daily_load else 0
    
    return TimelineAnalysis(
        start_date=timeline_start,
        end_date=timeline_end,
        duration_days=duration_days,
        avg_submissions_per_month=avg_daily_load * 30,  # Convert daily to monthly
        summary=f"Timeline spans {duration_days} days with peak load of {peak_daily_load} submissions"
    )

def analyze_resources(schedule: Dict[str, date], config: Config) -> ResourceAnalysis:
    """Analyze resource utilization patterns."""
    if not schedule:
            return ResourceAnalysis(
        peak_load=0,
        avg_load=0.0,
        utilization_pattern={},
        summary="No submissions to analyze"
    )
    
    # Calculate daily utilization using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return ResourceAnalysis(
            peak_load=0,
            avg_load=0.0,
            utilization_pattern={},
            summary="No active days in schedule"
        )
    
    peak_load = max(daily_load.values())
    avg_load = sum(daily_load.values()) / len(daily_load)
    
    return ResourceAnalysis(
        peak_load=peak_load,
        avg_load=avg_load,
        utilization_pattern=daily_load,
        summary=f"Peak load: {peak_load}, Avg: {avg_load:.1f}"
    ) 