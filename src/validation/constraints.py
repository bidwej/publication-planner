"""Constraint validation functions for dependencies and constraints."""

from typing import Dict, Any, List
from datetime import date

from src.core.models import Config, Submission, DependencyValidation, DependencyViolation, SubmissionType
from src.core.constants import QUALITY_CONSTANTS


def validate_dependency_satisfaction_complete(schedule: Dict[str, date], config: Config) -> DependencyValidation:
    """Validate that all dependencies are satisfied for complete schedule."""
    perfect_satisfaction_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DependencyValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            satisfaction_rate=perfect_satisfaction_rate,
            total_dependencies=0,
            satisfied_dependencies=0
        )
    
    violations = []
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.depends_on:
            continue
        
        for dep_id in sub.depends_on:
            total_dependencies += 1
            
            # Check if dependency exists in schedule
            if dep_id not in schedule:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not scheduled",
                    dependency_id=dep_id,
                    issue="missing_dependency",
                    severity="high"
                ))
                continue
            
            # Check if dependency is completed before this submission starts
            dep_start = schedule[dep_id]
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not found in submissions",
                    dependency_id=dep_id,
                    issue="invalid_dependency",
                    severity="high"
                ))
                continue
            
            dep_end = dep_sub.get_end_date(dep_start, config)
            
            if start_date < dep_end:
                days_violation = (dep_end - start_date).days
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Submission {sid} starts before dependency {dep_id} completes",
                    dependency_id=dep_id,
                    issue="timing_violation",
                    days_violation=days_violation,
                    severity="medium"
                ))
            else:
                satisfied_dependencies += 1
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * percentage_multiplier) if total_dependencies > 0 else perfect_satisfaction_rate
    is_valid = len(violations) == 0
    
    return DependencyValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"{satisfied_dependencies}/{total_dependencies} dependencies satisfied ({satisfaction_rate:.1f}%)",
        satisfaction_rate=satisfaction_rate,
        total_dependencies=total_dependencies,
        satisfied_dependencies=satisfied_dependencies
    )


def validate_dependencies_satisfied(sub: Submission, schedule: Dict[str, date], 
                                  submissions_dict: Dict[str, Submission], config: Config, 
                                  current_date: date) -> bool:
    """Check if all dependencies are satisfied for a single submission."""
    if not sub.depends_on:
        return True
    
    for dep_id in sub.depends_on:
        # Check if dependency exists
        if dep_id not in submissions_dict:
            return False
        
        # Check if dependency is scheduled
        if dep_id not in schedule:
            return False
        
        # Check if dependency is completed
        dep = submissions_dict[dep_id]
        dep_start = schedule[dep_id]
        dep_end = dep.get_end_date(dep_start, config)
        
        if current_date < dep_end:
            return False
    
    return True


def validate_abstract_paper_dependencies(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate abstract-paper dependencies."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        if not sub.conference_id:
            continue
        
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf or not conf.requires_abstract_before_paper():
            continue
        
        total_papers += 1
        
        # Check if required abstract exists and is scheduled
        abstract_id = f"{sid}_abstract_{sub.conference_id}"
        
        if abstract_id not in schedule:
            violations.append({
                "submission_id": sid,
                "description": f"Paper {sid} requires abstract {abstract_id} but it's not scheduled",
                "severity": "high",
                "missing_abstract": abstract_id
            })
            continue
        
        # Check if abstract is completed before paper starts
        abstract_sub = config.submissions_dict.get(abstract_id)
        if not abstract_sub:
            violations.append({
                "submission_id": sid,
                "description": f"Abstract {abstract_id} not found in submissions",
                "severity": "high",
                "missing_abstract": abstract_id
            })
            continue
        
        abstract_start = schedule[abstract_id]
        abstract_end = abstract_sub.get_end_date(abstract_start, config)
        
        if start_date < abstract_end:
            days_violation = (abstract_end - start_date).days
            violations.append({
                "submission_id": sid,
                "description": f"Paper {sid} starts before abstract {abstract_id} completes ({days_violation} days early)",
                "severity": "medium",
                "days_violation": days_violation
            })
        else:
            compliant_papers += 1
    
    compliance_rate = (compliant_papers / total_papers * QUALITY_CONSTANTS.percentage_multiplier) if total_papers > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_papers": total_papers,
        "compliant_papers": compliant_papers,
        "summary": f"Abstract-paper dependencies: {compliant_papers}/{total_papers} papers compliant ({compliance_rate:.1f}%)"
    }
