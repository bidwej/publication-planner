"""Generate comprehensive schedule reports for presentation."""

from __future__ import annotations
from typing import Dict, Any
from datetime import date
from core.types import Config
from metrics.constraints import validate_deadline_compliance, validate_dependency_satisfaction, validate_resource_constraints
from metrics.scoring import calculate_penalty_score
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
        len(deadline_validation["violations"]) +
        len(dependency_validation["violations"]) +
        len(resource_validation["violations"])
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
            "deadlines": deadline_validation,
            "dependencies": dependency_validation,
            "resources": resource_validation
        },
        "scoring": {
            "total_penalty": penalty_breakdown.total_penalty,
            "deadline_penalties": penalty_breakdown.deadline_penalties,
            "dependency_penalties": penalty_breakdown.dependency_penalties,
            "resource_penalties": penalty_breakdown.resource_penalties
        },
        "timeline": timeline,
        "resources": resources
    }

def calculate_overall_score(deadline_validation: Dict, dependency_validation: Dict, 
                          resource_validation: Dict, penalty_breakdown: Any) -> float:
    """Calculate overall schedule score (0-100)."""
    # Base score from constraint compliance
    deadline_score = deadline_validation.get("compliance_rate", 100.0)
    dependency_score = dependency_validation.get("satisfaction_rate", 100.0)
    resource_score = 100.0 if resource_validation.get("is_valid", True) else 50.0
    
    # Penalty adjustment
    max_penalty = 10000.0
    penalty_score = max(0, 100 - (penalty_breakdown.total_penalty / max_penalty * 100))
    
    # Weighted average
    weights = {
        "deadline": 0.4,
        "dependency": 0.3,
        "resource": 0.2,
        "penalty": 0.1
    }
    
    overall_score = (
        deadline_score * weights["deadline"] +
        dependency_score * weights["dependency"] +
        resource_score * weights["resource"] +
        penalty_score * weights["penalty"]
    )
    
    return min(100.0, max(0.0, overall_score)) 