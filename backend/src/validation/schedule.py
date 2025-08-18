"""Schedule validation functions for comprehensive schedule constraints."""

from typing import Dict, Any
from datetime import date

from ..core.models import Config, Schedule
from .deadline import validate_deadline_constraints
from .resources import validate_resources_constraints
from .venue import validate_venue_constraints


def validate_schedule(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate comprehensive schedule constraints."""
    if not schedule:
        return {"is_valid": False, "violations": [], "summary": "No schedule to validate"}
    
    # Validate all constraint types
    deadline_result = validate_deadline_constraints(schedule, config)
    resource_result = validate_resources_constraints(schedule, config)
    venue_result = validate_venue_constraints(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.get("violations", []) + 
        resource_result.get("violations", []) + 
        venue_result.get("violations", [])
    )
    
    # Calculate totals
    total_submissions = len(schedule.intervals)
    compliant_submissions = sum([
        deadline_result.get("compliant_submissions", 0),
        resource_result.get("compliant_submissions", 0),
        venue_result.get("compliant_submissions", 0)
    ])
    
    # Overall validation
    is_valid = len(all_violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": all_violations,
        "summary": f"Schedule validation: {len(all_violations)} violations found",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions,
        "constraints": {
            "deadline": deadline_result,
            "resources": resource_result,
            "venue": venue_result
        }
    }


def _validate_blackout_dates(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate blackout date constraints."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.earliest_start_date:
            continue
        
        total_submissions += 1
        days_diff = abs((interval.start_date - sub.earliest_start_date).days)
        
        if days_diff > 60:
            violations.append({
                "submission_id": sid,
                "description": f"Submission scheduled {days_diff} days from earliest start date (max 60 days)",
                "severity": "medium",
                "days_violation": days_diff - 60,
                "earliest_start_date": sub.earliest_start_date,
                "scheduled_date": interval.start_date
            })
        else:
            compliant_submissions += 1
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions within blackout constraints",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions
    }


def _validate_paper_lead_time(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate paper lead time constraints."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.earliest_start_date:
            continue
        
        total_submissions += 1
        days_diff = abs((interval.start_date - sub.earliest_start_date).days)
        
        if days_diff > 60:
            violations.append({
                "submission_id": sid,
                "description": f"Submission scheduled {days_diff} days from earliest start date (max 60 days)",
                "severity": "medium",
                "days_violation": days_diff - 60,
                "earliest_start_date": sub.earliest_start_date,
                "scheduled_date": interval.start_date
            })
        else:
            compliant_submissions += 1
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions within lead time constraints",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions
    }


def _validate_dependency_satisfaction(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate dependency satisfaction constraints."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.dependencies:
            total_submissions += 1
            compliant_submissions += 1
            continue
        
        total_submissions += 1
        is_compliant = True
        
        for dep_id in sub.dependencies:
            if dep_id not in schedule.intervals:
                violations.append({
                    "submission_id": sid,
                    "description": f"Dependency {dep_id} not found in schedule",
                    "severity": "high",
                    "dependency_id": dep_id
                })
                is_compliant = False
                break
            
            dep_interval = schedule.intervals[dep_id]
            if interval.start_date <= dep_interval.start_date:
                violations.append({
                    "submission_id": sid,
                    "description": f"Submission scheduled before dependency {dep_id}",
                    "severity": "high",
                    "dependency_id": dep_id,
                    "scheduled_date": interval.start_date,
                    "dependency_date": dep_interval.start_date
                })
                is_compliant = False
                break
        
        if is_compliant:
            compliant_submissions += 1
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions satisfy dependencies",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions
    }
