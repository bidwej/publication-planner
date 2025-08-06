"""Efficiency scoring functions."""

from typing import Dict, List
from datetime import date, timedelta
from collections import defaultdict

from core.models import Config, EfficiencyMetrics, TimelineMetrics
from core.constants import (
    MAX_SCORE, MIN_SCORE, PERCENTAGE_MULTIPLIER, OPTIMAL_UTILIZATION_RATE,
    UTILIZATION_DEVIATION_PENALTY, TIMELINE_EFFICIENCY_SHORT_PENALTY,
    TIMELINE_EFFICIENCY_LONG_PENALTY, IDEAL_DAYS_PER_SUBMISSION
)


def calculate_efficiency_score(schedule: Dict[str, date], config: Config) -> float:
    """
    Calculate efficiency score based on resource utilization and timeline.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    float
        Efficiency score (0-100)
    """
    if not schedule:
        return MIN_SCORE
    
    # Calculate resource efficiency
    resource_metrics = calculate_efficiency_resource(schedule, config)
    
    # Calculate timeline efficiency
    timeline_metrics = calculate_efficiency_timeline(schedule, config)
    
    # Combine scores (weighted average)
    resource_weight = 0.6
    timeline_weight = 0.4
    
    efficiency_score = (
        resource_metrics.efficiency_score * resource_weight +
        timeline_metrics.timeline_efficiency * timeline_weight
    )
    
    return max(MIN_SCORE, min(MAX_SCORE, efficiency_score))


def calculate_efficiency_resource(schedule: Dict[str, date], config: Config) -> EfficiencyMetrics:
    """
    Calculate detailed resource efficiency metrics.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    EfficiencyMetrics
        Resource efficiency metrics
    """
    if not schedule:
        return EfficiencyMetrics(
            utilization_rate=MIN_SCORE,
            peak_utilization=0,
            avg_utilization=MIN_SCORE,
            efficiency_score=MIN_SCORE
        )
    
    # Calculate daily load
    daily_load = defaultdict(int)
    submissions_dict = config.submissions_dict
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission:
            continue
            
        # Calculate duration and add to daily load
        duration_days = submission.get_duration_days(config)
        for i in range(duration_days):
            current_date = start_date + timedelta(days=i)
            daily_load[current_date] += 1
    
    if not daily_load:
        return EfficiencyMetrics(
            utilization_rate=MIN_SCORE,
            peak_utilization=0,
            avg_utilization=MIN_SCORE,
            efficiency_score=MIN_SCORE
        )
    
    # Calculate metrics
    peak_utilization = max(daily_load.values())
    avg_utilization = sum(daily_load.values()) / len(daily_load)
    max_concurrent = config.max_concurrent_submissions
    
    # Calculate utilization rate
    utilization_rate = (avg_utilization / max_concurrent) * PERCENTAGE_MULTIPLIER if max_concurrent > 0 else MIN_SCORE
    
    # Calculate efficiency score (penalize both under-utilization and over-utilization)
    if max_concurrent > 0:
        # Optimal utilization is around 80% of max capacity
        optimal_utilization = max_concurrent * OPTIMAL_UTILIZATION_RATE
        utilization_deviation = abs(avg_utilization - optimal_utilization) / optimal_utilization
        efficiency_score = max(MIN_SCORE, MAX_SCORE - (utilization_deviation * UTILIZATION_DEVIATION_PENALTY))
    else:
        efficiency_score = MIN_SCORE
    
    return EfficiencyMetrics(
        utilization_rate=utilization_rate,
        peak_utilization=peak_utilization,
        avg_utilization=avg_utilization,
        efficiency_score=efficiency_score
    )


def calculate_efficiency_timeline(schedule: Dict[str, date], config: Config) -> TimelineMetrics:
    """
    Calculate timeline efficiency metrics.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Mapping of submission_id to start_date
    config : Config
        Configuration object
        
    Returns
    -------
    TimelineMetrics
        Timeline efficiency metrics
    """
    if not schedule:
        return TimelineMetrics(
            duration_days=0,
            avg_daily_load=MIN_SCORE,
            timeline_efficiency=MIN_SCORE
        )
    
    # Calculate timeline span
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    duration_days = (end_date - start_date).days + 1
    
    # Calculate average daily load
    total_submissions = len(schedule)
    avg_daily_load = total_submissions / duration_days if duration_days > 0 else MIN_SCORE
    
    # Calculate timeline efficiency (penalize very long or very short timelines)
    total_submissions_count = len(config.submissions)
    if total_submissions_count > 0:
        # Ideal timeline should be proportional to number of submissions
        ideal_duration = total_submissions_count * IDEAL_DAYS_PER_SUBMISSION  # Assume 30 days per submission
        duration_ratio = duration_days / ideal_duration if ideal_duration > 0 else 1.0
        
        # Efficiency decreases as we deviate from ideal duration
        if duration_ratio <= 1.0:
            # Shorter than ideal is better than longer
            timeline_efficiency = MAX_SCORE * (1.0 - (1.0 - duration_ratio) * TIMELINE_EFFICIENCY_SHORT_PENALTY)
        else:
            # Longer than ideal gets penalized more
            timeline_efficiency = MAX_SCORE * (1.0 - (duration_ratio - 1.0) * TIMELINE_EFFICIENCY_LONG_PENALTY)
        
        timeline_efficiency = max(MIN_SCORE, min(MAX_SCORE, timeline_efficiency))
    else:
        timeline_efficiency = MIN_SCORE
    
    return TimelineMetrics(
        duration_days=duration_days,
        avg_daily_load=avg_daily_load,
        timeline_efficiency=timeline_efficiency
    ) 