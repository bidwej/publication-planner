"""Schedule metrics calculation functions."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config
from src.scoring.penalties import calculate_penalty_score
from src.scoring.quality import calculate_quality_score
from src.scoring.efficiency import calculate_efficiency_score


def get_schedule_metrics(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """
    Get comprehensive metrics for a schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        The schedule to analyze
    config : Config
        The configuration to use for analysis
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing various schedule metrics
    """
    # Calculate scores
    penalty_breakdown = calculate_penalty_score(schedule, config)
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    
    # Calculate basic metrics
    total_submissions = len(schedule)
    if schedule:
        # Handle both string and date objects
        start_dates = []
        end_dates = []
        
        for date_val in schedule.values():
            if isinstance(date_val, str):
                from datetime import datetime
                parsed_date = datetime.strptime(date_val, "%Y-%m-%d").date()
                start_dates.append(parsed_date)
                end_dates.append(parsed_date)
            else:
                start_dates.append(date_val)
                end_dates.append(date_val)
        
        if start_dates:
            start_date = min(start_dates)
            end_date = max(end_dates)
            duration_days = (end_date - start_date).days
        else:
            duration_days = 0
    else:
        duration_days = 0
    
    return {
        "total_submissions": total_submissions,
        "duration_days": duration_days,
        "penalty_score": penalty_breakdown.total_penalty,
        "quality_score": quality_score,
        "efficiency_score": efficiency_score,
        "penalty_breakdown": {
            "deadline_penalties": penalty_breakdown.deadline_penalties,
            "dependency_penalties": penalty_breakdown.dependency_penalties,
            "resource_penalties": penalty_breakdown.resource_penalties
        }
    }
