"""Penalty validation functions for priority weighting."""

from typing import Dict, Any
from datetime import date, timedelta

from src.core.models import Config
from src.core.constants import QUALITY_CONSTANTS


def validate_priority_weighting(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate priority weighting in schedule."""
    violations = []
    total_submissions = 0
    properly_weighted = 0
    
    # Check if priority weights are configured
    if not config.priority_weights:
        return {
            "is_valid": True,
            "violations": [],
            "weighting_rate": QUALITY_CONSTANTS.perfect_compliance_rate,
            "total_submissions": 0,
            "properly_weighted": 0,
            "average_priority": 0.0,
            "summary": "No priority weights configured"
        }
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        
        # Check if high priority submissions are scheduled early
        # Use priority score to determine if this is a high priority submission
        priority_score = sub.get_priority_score(config)
        if priority_score > 1.5:  # High priority threshold
            # High priority submissions should be scheduled early
            # This is a simplified check - in practice, you might want more sophisticated logic
            early_threshold = date.today() + timedelta(days=30)  # Within 30 days
            
            if start_date > early_threshold:
                violations.append({
                    "submission_id": sid,
                    "description": f"High priority submission {sid} scheduled too late: {start_date}",
                    "severity": "medium",
                    "priority_score": priority_score,
                    "scheduled_date": start_date,
                    "early_threshold": early_threshold
                })
            else:
                properly_weighted += 1
        else:
            # Non-high priority submissions are considered properly weighted
            properly_weighted += 1
    
    weighting_rate = (properly_weighted / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    # Calculate average priority score
    total_priority_score = 0.0
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if sub:
            total_priority_score += sub.get_priority_score(config)
    
    average_priority = total_priority_score / total_submissions if total_submissions > 0 else 0.0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "weighting_rate": weighting_rate,
        "total_submissions": total_submissions,
        "properly_weighted": properly_weighted,
        "average_priority": average_priority,
        "summary": f"Priority weighting: {properly_weighted}/{total_submissions} submissions properly weighted ({weighting_rate:.1f}%)"
    }
