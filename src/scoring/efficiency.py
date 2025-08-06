"""Calculate efficiency metrics for schedules."""

from __future__ import annotations
from typing import Dict
from datetime import date
from core.models import Config, EfficiencyMetrics, TimelineMetrics
from core.constraints import _calculate_daily_load

def calculate_efficiency_score(schedule: Dict[str, date], config: Config) -> float:
    """Calculate efficiency score based on resource utilization and timeline."""
    if not schedule:
        return 0.0
    
    # Calculate resource utilization using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    max_concurrent = config.max_concurrent_submissions
    
    if not daily_load:
        return 0.0
    
    # Calculate efficiency metrics
    total_load = sum(daily_load.values())
    total_capacity = len(daily_load) * max_concurrent
    utilization_rate = (total_load / total_capacity * 100) if total_capacity > 0 else 0.0
    
    # Timeline efficiency (shorter is better, but with minimum threshold)
    dates = list(schedule.values())
    duration_days = (max(dates) - min(dates)).days if dates else 0
    min_duration = len(schedule) * 30  # Minimum reasonable duration
    timeline_efficiency = max(0, 100 - (duration_days - min_duration) / min_duration * 100) if min_duration > 0 else 100
    
    # Combined efficiency score
    efficiency_score = (utilization_rate * 0.6 + timeline_efficiency * 0.4)
    
    return min(100.0, max(0.0, efficiency_score))

def calculate_efficiency_resource(schedule: Dict[str, date], config: Config) -> EfficiencyMetrics:
    """Calculate detailed resource efficiency metrics."""
    if not schedule:
        return EfficiencyMetrics(
            utilization_rate=0.0,
            peak_utilization=0,
            avg_utilization=0.0,
            efficiency_score=0.0
        )
    
    # Calculate daily workload using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    max_concurrent = config.max_concurrent_submissions
    
    if not daily_load:
        return EfficiencyMetrics(
            utilization_rate=0.0,
            peak_utilization=0,
            avg_utilization=0.0,
            efficiency_score=0.0
        )
    
    # Calculate metrics
    total_load = sum(daily_load.values())
    total_capacity = len(daily_load) * max_concurrent
    utilization_rate = (total_load / total_capacity * 100) if total_capacity > 0 else 0.0
    peak_utilization = max(daily_load.values())
    avg_utilization = total_load / len(daily_load) if daily_load else 0
    
    # Efficiency score (penalize over-utilization and under-utilization)
    target_utilization = 80.0  # Target 80% utilization
    utilization_penalty = abs(utilization_rate - target_utilization) / target_utilization * 100
    efficiency_score = max(0, 100 - utilization_penalty)
    
    return EfficiencyMetrics(
        utilization_rate=utilization_rate,
        peak_utilization=peak_utilization,
        avg_utilization=avg_utilization,
        efficiency_score=efficiency_score
    )

def calculate_efficiency_timeline(schedule: Dict[str, date], config: Config) -> TimelineMetrics:
    """Calculate timeline efficiency metrics."""
    if not schedule:
        return TimelineMetrics(
            duration_days=0,
            avg_daily_load=0.0,
            timeline_efficiency=0.0
        )
    
    # Calculate timeline metrics
    dates = list(schedule.values())
    duration_days = (max(dates) - min(dates)).days if dates else 0
    
    # Calculate daily workload using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    
    avg_daily_load = sum(daily_load.values()) / len(daily_load) if daily_load else 0
    
    # Timeline efficiency (optimal duration vs actual)
    total_submissions = len(schedule)
    optimal_duration = total_submissions * 30  # Assume 30 days per submission
    timeline_efficiency = max(0, 100 - abs(duration_days - optimal_duration) / optimal_duration * 100) if optimal_duration > 0 else 100
    
    return TimelineMetrics(
        duration_days=duration_days,
        avg_daily_load=avg_daily_load,
        timeline_efficiency=timeline_efficiency
    ) 