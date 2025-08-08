"""Recurrence validation functions for soft block model."""

from typing import Dict, Any
from datetime import date, timedelta

from src.core.models import Config
from src.core.constants import QUALITY_CONSTANTS


def validate_soft_block_model(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate soft block model (PCCP) with ±2 month window."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    # Check if soft block model is enabled
    if config.scheduling_options and not config.scheduling_options.get("enable_soft_block_model", True):
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": QUALITY_CONSTANTS.perfect_compliance_rate,
            "summary": "Soft block model disabled"
        }
    
    # Group submissions by conference
    conference_submissions = {}
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf_id = sub.conference_id
        
        if conf_id not in conference_submissions:
            conference_submissions[conf_id] = []
        
        conference_submissions[conf_id].append({
            "submission_id": sid,
            "start_date": start_date,
            "submission": sub
        })
    
    # Check each conference for soft block violations
    for conf_id, submissions in conference_submissions.items():
        if len(submissions) <= 1:
            # Only one submission to this conference, no soft block issues
            compliant_submissions += len(submissions)
            continue
        
        # Sort submissions by start date
        submissions.sort(key=lambda x: x["start_date"])
        
        # Check for submissions within ±2 months (60 days) of each other
        for i in range(len(submissions)):
            current = submissions[i]
            current_date = current["start_date"]
            
            # Check submissions before current
            for j in range(i):
                prev = submissions[j]
                prev_date = prev["start_date"]
                days_between = (current_date - prev_date).days
                
                if days_between <= 60:  # Within 2 months
                    violations.append({
                        "submission_id": current["submission_id"],
                        "description": f"Soft block violation: {current['submission_id']} scheduled {days_between} days after {prev['submission_id']} to same conference {conf_id}",
                        "severity": "medium",
                        "conference_id": conf_id,
                        "first_submission": prev["submission_id"],
                        "second_submission": current["submission_id"],
                        "days_between": days_between
                    })
                    break
            else:
                # No violations found for this submission
                compliant_submissions += 1
    
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_mods": total_submissions,
        "compliant_mods": compliant_submissions,
        "summary": f"Soft block model: {compliant_submissions}/{total_submissions} submissions compliant ({compliance_rate:.1f}%)"
    }
