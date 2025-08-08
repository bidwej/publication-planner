"""Dependency validation functions for submission relationships."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission, DependencyValidation, DependencyViolation, SubmissionType
from src.core.constants import QUALITY_CONSTANTS


def validate_dependency_satisfaction(schedule: Dict[str, date], config: Config) -> DependencyValidation:
    """Validate that all dependencies are satisfied."""
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DependencyValidation(
            is_valid=True,
            violations=[],
            summary="No dependencies to validate",
            satisfaction_rate=perfect_compliance_rate,
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
                    description=f"Dependency {dep_id} is not scheduled",
                    severity="high",
                    dependency_id=dep_id,
                    issue="missing_dependency"
                ))
                continue
            
            # Check if dependency is satisfied
            dep_start = schedule[dep_id]
            dep_sub = config.submissions_dict.get(dep_id)
            if not dep_sub:
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} not found in config",
                    severity="high",
                    dependency_id=dep_id,
                    issue="invalid_dependency"
                ))
                continue
            
            # Calculate dependency end date using submission method
            dep_end = dep_sub.get_end_date(dep_start, config)
            
            # Check if dependency is completed before this submission starts
            if dep_end > start_date:
                days_violation = (dep_end - start_date).days
                violations.append(DependencyViolation(
                    submission_id=sid,
                    description=f"Dependency {dep_id} ends {days_violation} days after submission {sid} starts",
                    severity="medium",
                    dependency_id=dep_id,
                    issue="timing_violation",
                    days_violation=days_violation
                ))
            else:
                satisfied_dependencies += 1
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * percentage_multiplier) if total_dependencies > 0 else perfect_compliance_rate
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
                                 submissions: Dict[str, Submission], config: Config, current: date) -> bool:
    """Validate that all dependencies for a single submission are satisfied."""
    if not sub.depends_on:
        return True
    
    for dep_id in sub.depends_on:
        if dep_id not in schedule:
            return False
        
        dep_sub = submissions.get(dep_id)
        if not dep_sub:
            return False
        
        dep_start = schedule[dep_id]
        dep_end = dep_sub.get_end_date(dep_start, config)
        
        # Check if dependency is completed before current date
        if dep_end > current:
            return False
    
    return True


def validate_abstract_paper_dependencies(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate abstract-paper dependency relationships."""
    violations = []
    total_papers = 0
    valid_papers = 0
    
    for sid in schedule:
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER or not sub.conference_id:
            continue
        
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf or not conf.requires_abstract_before_paper():
            continue
        
        total_papers += 1
        
        # Check if required abstract exists and is scheduled
        from src.core.models import generate_abstract_id
        abstract_id = generate_abstract_id(sub.id, sub.conference_id)
        abstract = config.submissions_dict.get(abstract_id)
        
        if not abstract:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "missing_abstract_id": abstract_id,
                "description": f"Paper {sid} requires abstract {abstract_id} for conference {sub.conference_id}"
            })
            continue
        
        if abstract_id not in schedule:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "missing_abstract_id": abstract_id,
                "description": f"Paper {sid} requires abstract {abstract_id} to be scheduled"
            })
            continue
        
        # Check if paper is scheduled after abstract
        paper_start = schedule[sid]
        abstract_start = schedule[abstract_id]
        
        if paper_start <= abstract_start:
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "abstract_id": abstract_id,
                "paper_start": paper_start.isoformat(),
                "abstract_start": abstract_start.isoformat(),
                "description": f"Paper {sid} must be scheduled after abstract {abstract_id}"
            })
            continue
        
        # Check if paper depends on abstract
        if abstract_id not in (sub.depends_on or []):
            violations.append({
                "submission_id": sid,
                "conference_id": sub.conference_id,
                "abstract_id": abstract_id,
                "description": f"Paper {sid} must depend on abstract {abstract_id}"
            })
            continue
        
        valid_papers += 1
    
    dependency_rate = (valid_papers / total_papers * QUALITY_CONSTANTS.percentage_multiplier) if total_papers > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return {
        "is_valid": len(violations) == 0,
        "violations": violations,
        "dependency_rate": dependency_rate,
        "total_papers": total_papers,
        "valid_papers": valid_papers,
        "summary": f"Abstract-paper dependencies: {valid_papers}/{total_papers} papers valid ({dependency_rate:.1f}%)"
    }
