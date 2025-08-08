"""Generate comprehensive schedule reports for presentation."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date
from src.core.models import Config
from src.validation.deadline import validate_deadline_constraints
from src.validation.schedule import validate_schedule_constraints
from src.validation.resources import validate_resources_constraints
from src.scoring.penalties import calculate_penalty_score
from src.analytics.analytics import analyze_timeline, analyze_resources
from src.core.constants import (
    REPORT_CONSTANTS
)

def generate_schedule_report(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Generate a comprehensive schedule report for presentation."""
    if not schedule:
        return {
            "summary": {
                "is_feasible": True,
                "total_violations": 0,
                "overall_score": REPORT_CONSTANTS.max_score,
                "total_submissions": 0
            },
            "constraints": {},
            "scoring": {},
            "timeline": {},
            "resources": {}
        }
    
    # Validate all constraints using the main validation function
    validation_result = validate_schedule_constraints(schedule, config)
    deadline_validation = validation_result["constraints"]["deadlines"]
    dependency_validation = validation_result["constraints"]["dependencies"]
    resource_validation = validation_result["constraints"]["resources"]
    
    # Calculate scores
    penalty_breakdown = calculate_penalty_score(schedule, config)
    
    # Analyze timeline
    timeline = analyze_timeline(schedule, config)
    
    # Analyze resources
    resources = analyze_resources(schedule, config)
    
    # Overall assessment
    total_violations = (
        len(deadline_validation.get("violations", [])) +
        len(dependency_validation.get("violations", [])) +
        len(resource_validation.get("violations", []))
    )
    
    is_feasible = total_violations == 0
    overall_score = calculate_overall_score(deadline_validation, dependency_validation, resource_validation, penalty_breakdown)
    
    return {
        "summary": {
            "is_feasible": is_feasible,
            "total_violations": total_violations,
            "overall_score": overall_score,
            "total_submissions": len(schedule)
        },
        "constraints": {
            "deadlines": {
                "is_valid": deadline_validation.get("is_valid", True),
                "compliance_rate": deadline_validation.get("compliance_rate", 100.0),
                "total_submissions": deadline_validation.get("total_submissions", 0),
                "compliant_submissions": deadline_validation.get("compliant_submissions", 0),
                "violations": deadline_validation.get("violations", []),
                "summary": deadline_validation.get("summary", "")
            },
            "dependencies": {
                "is_valid": dependency_validation.get("is_valid", True),
                "satisfaction_rate": dependency_validation.get("satisfaction_rate", 100.0),
                "total_dependencies": dependency_validation.get("total_dependencies", 0),
                "satisfied_dependencies": dependency_validation.get("satisfied_dependencies", 0),
                "violations": dependency_validation.get("violations", []),
                "summary": dependency_validation.get("summary", "")
            },
            "resources": {
                "is_valid": resource_validation.get("is_valid", True),
                "max_concurrent": resource_validation.get("max_concurrent", 0),
                "max_observed": resource_validation.get("max_observed", 0),
                "total_days": resource_validation.get("total_days", 0),
                "violations": resource_validation.get("violations", []),
                "summary": resource_validation.get("summary", "")
            }
        },
        "scoring": {
            "total_penalty": penalty_breakdown.total_penalty,
            "deadline_penalties": penalty_breakdown.deadline_penalties,
            "dependency_penalties": penalty_breakdown.dependency_penalties,
            "resource_penalties": penalty_breakdown.resource_penalties
        },
        "timeline": {
            "start_date": timeline.start_date,
            "end_date": timeline.end_date,
            "duration_days": timeline.duration_days,
            "avg_submissions_per_month": timeline.avg_submissions_per_month,
            "summary": timeline.summary
        },
        "resources": {
            "peak_load": resources.peak_load,
            "avg_load": resources.avg_load,
            "utilization_pattern": resources.utilization_pattern,
            "summary": resources.summary
        }
    }

def calculate_overall_score(deadline_validation, dependency_validation, 
                          resource_validation, penalty_breakdown) -> float:
    """Calculate an overall score for the schedule (0.0 to 1.0)."""
    # Base score starts at 1.0
    score = 1.0
    
    # Deduct for violations (normalized)
    score -= len(deadline_validation.get("violations", [])) * REPORT_CONSTANTS.deadline_violation_penalty
    score -= len(dependency_validation.get("violations", [])) * REPORT_CONSTANTS.dependency_violation_penalty
    score -= len(resource_validation.get("violations", [])) * REPORT_CONSTANTS.resource_violation_penalty
    
    # Deduct for penalty costs (normalized)
    penalty_factor = min(penalty_breakdown.total_penalty / REPORT_CONSTANTS.penalty_normalization_factor, REPORT_CONSTANTS.max_penalty_factor)  # Cap at max_penalty_factor
    score -= penalty_factor
    
    # Bonus for high compliance rates (but cap at 1.0)
    if deadline_validation.get("compliance_rate", 100) > 95:
        score += 0.05
    if dependency_validation.get("satisfaction_rate", 100) > 95:
        score += 0.05
    
    # Clamp between min_score and max_score
    return max(min(score, 1.0), REPORT_CONSTANTS.min_score) 