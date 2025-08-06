"""Generate comprehensive schedule reports for presentation."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date
from ..core.models import Config
from ..core.constraints import validate_deadline_compliance, validate_dependency_satisfaction, validate_resource_constraints
from ..scoring.penalty import calculate_penalty_score
from .analytics import analyze_timeline, analyze_resources

def generate_schedule_report(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Generate a comprehensive schedule report for presentation."""
    if not schedule:
        return {
            "summary": "Empty schedule",
            "constraints": {},
            "scoring": {},
            "timeline": {},
            "resources": {}
        }
    
    # Validate constraints
    deadline_validation = validate_deadline_compliance(schedule, config)
    dependency_validation = validate_dependency_satisfaction(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    # Calculate scores
    penalty_breakdown = calculate_penalty_score(schedule, config)
    
    # Analyze timeline
    timeline = analyze_timeline(schedule, config)
    
    # Analyze resources
    resources = analyze_resources(schedule, config)
    
    # Overall assessment
    total_violations = (
        len(deadline_validation.violations) +
        len(dependency_validation.violations) +
        len(resource_validation.violations)
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
                "is_valid": deadline_validation.is_valid,
                "compliance_rate": deadline_validation.compliance_rate,
                "total_submissions": deadline_validation.total_submissions,
                "compliant_submissions": deadline_validation.compliant_submissions,
                "violations": [v.__dict__ for v in deadline_validation.violations],
                "summary": deadline_validation.summary
            },
            "dependencies": {
                "is_valid": dependency_validation.is_valid,
                "satisfaction_rate": dependency_validation.satisfaction_rate,
                "total_dependencies": dependency_validation.total_dependencies,
                "satisfied_dependencies": dependency_validation.satisfied_dependencies,
                "violations": [v.__dict__ for v in dependency_validation.violations],
                "summary": dependency_validation.summary
            },
            "resources": {
                "is_valid": resource_validation.is_valid,
                "max_concurrent": resource_validation.max_concurrent,
                "max_observed": resource_validation.max_observed,
                "total_days": resource_validation.total_days,
                "violations": [v.__dict__ for v in resource_validation.violations],
                "summary": resource_validation.summary
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
            "avg_daily_load": timeline.avg_daily_load,
            "peak_daily_load": timeline.peak_daily_load,
            "summary": timeline.summary
        },
        "resources": {
            "max_concurrent": resources.max_concurrent,
            "avg_concurrent": resources.avg_concurrent,
            "utilization_rate": resources.utilization_rate,
            "overload_days": resources.overload_days,
            "summary": resources.summary
        }
    }

def calculate_overall_score(deadline_validation, dependency_validation, 
                          resource_validation, penalty_breakdown) -> float:
    """Calculate an overall score for the schedule."""
    # Base score starts at 100
    score = 100.0
    
    # Deduct for violations
    score -= len(deadline_validation.violations) * 10
    score -= len(dependency_validation.violations) * 15
    score -= len(resource_validation.violations) * 20
    
    # Deduct for penalty costs (normalized)
    penalty_factor = min(penalty_breakdown.total_penalty / 1000.0, 50.0)  # Cap at 50 points
    score -= penalty_factor
    
    # Bonus for high compliance rates
    if deadline_validation.compliance_rate > 95:
        score += 5
    if dependency_validation.satisfaction_rate > 95:
        score += 5
    
    return max(score, 0.0)  # Don't go below 0 