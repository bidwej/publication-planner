"""Efficiency scoring functions."""

from typing import Dict
from datetime import date, timedelta, datetime
from collections import defaultdict
import statistics

from core.models import Config, ScheduleMetrics, Schedule, Interval
from typing import Optional
from core.constants import (
    EFFICIENCY_CONSTANTS, SCORING_CONSTANTS, REPORT_CONSTANTS, QUALITY_CONSTANTS
)



def calculate_efficiency_score(schedule: Schedule, config: Config) -> float:
    """
    Calculate efficiency score based on resource utilization and timeline.
    
    Parameters
    ----------
    schedule : Schedule
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    float
        Efficiency score (0-100)
    """
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    
    if not schedule:
        return min_score
    
    # Calculate resource efficiency
    resource_metrics = calculate_efficiency_resource(schedule, config)
    
    # Calculate timeline efficiency
    timeline_metrics = calculate_efficiency_timeline(schedule, config)
    
    # Handle None cases
    if resource_metrics is None or timeline_metrics is None:
        return min_score
    
    # Combine scores (weighted average)
    efficiency_score = (
        resource_metrics.efficiency_score * SCORING_CONSTANTS.efficiency_resource_weight +
        timeline_metrics.timeline_efficiency * SCORING_CONSTANTS.efficiency_timeline_weight
    )
    
    return max(min_score, min(max_score, efficiency_score))


def calculate_efficiency_resource(schedule: Schedule, config: Config) -> Optional[ScheduleMetrics]:
    """
    Calculate detailed resource efficiency metrics.
    
    Parameters
    ----------
    schedule : Schedule
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    ScheduleMetrics
        Resource efficiency metrics with utilization data
    """
    # Fixed scoring constants
    max_score = REPORT_CONSTANTS.max_score
    min_score = REPORT_CONSTANTS.min_score
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return None
    
    # Calculate daily load
    daily_load = defaultdict(int)
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if not submission:
            continue
            
        duration_days = submission.get_duration_days(config)
        for i in range(duration_days):
            current_date = interval.start_date + timedelta(days=i)
            daily_load[current_date] += 1
    
    if not daily_load:
        return None
    
    # Calculate metrics
    peak_utilization = max(daily_load.values())
    avg_utilization = statistics.mean(daily_load.values())
    max_concurrent = config.max_concurrent_submissions
    
    utilization_rate = (avg_utilization / max_concurrent) * percentage_multiplier if max_concurrent > 0 else min_score
    
    if max_concurrent > 0:
        optimal_utilization = max_concurrent * EFFICIENCY_CONSTANTS.optimal_utilization_rate
        utilization_deviation = abs(avg_utilization - optimal_utilization) / optimal_utilization
        efficiency_score = max(min_score, max_score - (utilization_deviation * EFFICIENCY_CONSTANTS.utilization_deviation_penalty))
    else:
        efficiency_score = min_score
    
    return ScheduleMetrics(
        avg_utilization=avg_utilization,
        peak_utilization=peak_utilization,
        utilization_rate=utilization_rate,
        efficiency_score=efficiency_score,
        duration_days=0,
        avg_daily_load=0.0,
        timeline_efficiency=0.0,
        makespan=0,
        total_penalty=0.0,
        compliance_rate=0.0,
        quality_score=0.0
    )





def calculate_efficiency_timeline(schedule: Schedule, config: Config) -> Optional[ScheduleMetrics]:
    """
    Calculate timeline efficiency metrics.
    
    Parameters
    ----------
    schedule : Schedule
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    ScheduleMetrics
        Timeline efficiency metrics with timeline data
    """
    # Fixed scoring constants
    max_score = 100.0
    min_score = 0.0
    
    if not schedule:
        return None
    
    # Calculate timeline span - handle both string and date objects
    start_dates = []
    end_dates = []
    
    for interval in schedule.intervals.values():
        start_dates.append(interval.start_date)
        end_dates.append(interval.end_date)
    
    if not start_dates:
        return None
    
    start_date = min(start_dates)
    end_date = max(end_dates)
    
    # Create a temporary schedule object to calculate duration
    temp_intervals = {str(i): Interval(start_date=d, end_date=d) for i, d in enumerate(start_dates)}
    temp_schedule = Schedule(intervals=temp_intervals)
    duration_days = temp_schedule.calculate_duration_days() + 1
    
    # Calculate average daily load
    total_submissions = len(schedule)
    avg_daily_load = total_submissions / duration_days if duration_days > 0 else min_score
    
    # Calculate timeline efficiency (penalize very long or very short timelines)
    total_submissions_count = len(config.submissions)
    if total_submissions_count > 0:
        # Ideal timeline should be proportional to number of submissions
        ideal_duration = total_submissions_count * EFFICIENCY_CONSTANTS.ideal_days_per_submission
        duration_ratio = duration_days / ideal_duration if ideal_duration > 0 else 1.0
        
        # Efficiency decreases as we deviate from ideal duration
        if duration_ratio <= 1.0:
            # Shorter than ideal is better than longer
            timeline_efficiency = max_score * (1.0 - (1.0 - duration_ratio) * EFFICIENCY_CONSTANTS.timeline_efficiency_short_penalty)
        else:
            # Longer than ideal gets penalized more
            timeline_efficiency = max_score * (1.0 - (duration_ratio - 1.0) * EFFICIENCY_CONSTANTS.timeline_efficiency_long_penalty)
        
        timeline_efficiency = max(min_score, min(max_score, timeline_efficiency))
    else:
        timeline_efficiency = min_score
    
    return ScheduleMetrics(
        avg_utilization=0.0,
        peak_utilization=0,
        utilization_rate=0.0,
        efficiency_score=0.0,
        duration_days=duration_days,
        avg_daily_load=avg_daily_load,
        timeline_efficiency=timeline_efficiency,
        makespan=0,
        total_penalty=0.0,
        compliance_rate=0.0,
        quality_score=0.0
    ) 
