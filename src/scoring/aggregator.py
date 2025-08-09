"""Schedule aggregator functions - combines all scoring functions plus basic schedule statistics."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config
from src.core.dates import calculate_schedule_duration
from src.scoring.penalties import calculate_penalty_score
from src.scoring.quality import calculate_quality_score
from src.scoring.efficiency import calculate_efficiency_score


def calculate_schedule_aggregation(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """
    Calculate comprehensive schedule aggregation - SINGLE PUBLIC FUNCTION.
    
    Simply calls the one public function from each scoring module and combines results.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        The schedule to analyze
    config : Config
        The configuration to use for analysis
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing comprehensive schedule metrics and scores
    """
    # Call one public function per scoring module
    penalty_breakdown = calculate_penalty_score(schedule, config)
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    
    # Add basic schedule statistics using shared utility
    total_submissions = len(schedule)
    duration_days = calculate_schedule_duration(schedule)
    
    return {
        "total_submissions": total_submissions,
        "duration_days": duration_days,
        "penalty_score": penalty_breakdown.total_penalty,
        "quality_score": quality_score,
        "efficiency_score": efficiency_score,
        "penalty_breakdown": penalty_breakdown
    }
