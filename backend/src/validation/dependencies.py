"""Dependency validation functions for submission ordering constraints."""

from typing import Dict, Any, List
from datetime import date, timedelta

from src.core.models import Config, Schedule, SubmissionType, ValidationResult, ConstraintViolation
from src.core.constants import QUALITY_CONSTANTS


def validate_dependency_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate that all dependencies are satisfied for entire schedule."""
    if not schedule:
        return ValidationResult(
            is_valid=True, 
            violations=[], 
            summary="No submissions to validate",
            metadata={
                "satisfaction_rate": QUALITY_CONSTANTS.perfect_compliance_rate, 
                "total_dependencies": 0, 
                "satisfied_dependencies": 0
            }
        )
    
    violations = []
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.depends_on:
            continue
        
        for dep_id in sub.depends_on:
            total_dependencies += 1
            
            if not sub.are_dependencies_satisfied(schedule, config, interval.start_date):
                if dep_id not in schedule.intervals:
                    violations.append({
                        "submission_id": sid, 
                        "description": f"Dependency {dep_id} not scheduled",
                        "dependency_id": dep_id, 
                        "issue": "missing_dependency", 
                        "severity": "high"
                    })
                elif not config.has_submission(dep_id):
                    violations.append({
                        "submission_id": sid, 
                        "description": f"Dependency {dep_id} not found in submissions",
                        "dependency_id": dep_id, 
                        "issue": "invalid_dependency", 
                        "severity": "high"
                    })
                else:
                    dep_start = schedule.intervals[dep_id].start_date
                    dep_sub = config.get_submission(dep_id)
                    dep_end = dep_sub.get_end_date(dep_start, config)
                    days_violation = (dep_end - interval.start_date).days
                    violations.append({
                        "submission_id": sid, 
                        "description": f"Submission {sid} starts before dependency {dep_id} completes",
                        "days_violation": days_violation, 
                        "severity": "medium"
                    })
            else:
                satisfied_dependencies += 1
    
    # Also validate abstract-paper dependencies
    abstract_paper_result = _validate_abstract_paper_dependencies(schedule, config)
    violations.extend(abstract_paper_result.violations)
    
    # Update totals
    total_dependencies += abstract_paper_result.metadata.get("total_dependencies", 0)
    satisfied_dependencies += abstract_paper_result.metadata.get("satisfied_dependencies", 0)
    
    satisfaction_rate = (satisfied_dependencies / total_dependencies * QUALITY_CONSTANTS.percentage_multiplier) if total_dependencies > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{satisfied_dependencies}/{total_dependencies} dependencies satisfied ({satisfaction_rate:.1f}%)",
        metadata={
            "total_dependencies": total_dependencies, 
            "satisfied_dependencies": satisfied_dependencies
        }
    )


def _validate_abstract_paper_dependencies(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate abstract-paper dependency relationships."""
    violations = []
    total_dependencies = 0
    satisfied_dependencies = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        paper_base_id = sid.split('-pap-')[0] if '-pap-' in sid else None
        conference_id = sid.split('-pap-')[1] if '-pap-' in sid else None
        
        if not paper_base_id or not conference_id:
            continue
        
        abstract_id = f"{paper_base_id}-abs-{conference_id}"
        
        if abstract_id in schedule.intervals:
            total_dependencies += 1
            abstract_start = schedule.intervals[abstract_id].start_date
            abstract_sub = config.get_submission(abstract_id)
            
            if abstract_sub:
                abstract_duration = abstract_sub.get_duration_days(config)
                abstract_end = abstract_start + timedelta(days=abstract_duration)
                
                if interval.start_date < abstract_end:
                    days_violation = (abstract_end - interval.start_date).days
                    violations.append(ConstraintViolation(
                        submission_id=sid, 
                        description=f"Paper starts before abstract completes",
                        severity="high"
                    ))
                else:
                    satisfied_dependencies += 1
            else:
                violations.append(ConstraintViolation(
                    submission_id=sid, 
                    description=f"Abstract {abstract_id} not found in submissions",
                    severity="high"
                ))
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{satisfied_dependencies}/{total_dependencies} abstract-paper dependencies satisfied",
        metadata={
            "total_dependencies": total_dependencies, 
            "satisfied_dependencies": satisfied_dependencies
        }
    )
