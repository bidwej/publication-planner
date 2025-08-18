"""Deadline validation functions for submission timing constraints."""

from typing import Dict, Any, List
from datetime import date, timedelta

from ..core.models import Config, Submission, DeadlineViolation, SubmissionType, Schedule, ConstraintViolation, ValidationResult
from ..core.constants import QUALITY_CONSTANTS, SCHEDULING_CONSTANTS


def validate_deadline_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate all deadline constraints for the complete schedule."""
    if not schedule:
        return ValidationResult(
            is_valid=True, 
            violations=[], 
            summary="No schedule to validate",
            metadata={
                "compliance_rate": QUALITY_CONSTANTS.perfect_compliance_rate, 
                "total_submissions": 0, 
                "compliant_submissions": 0
            }
        )
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        total_submissions += 1
        
        # Check if submission meets its deadline
        if not _validate_deadline_compliance_single(interval.start_date, sub, config):
            end_date = sub.get_end_date(interval.start_date, config)
            if sub.conference_id and config.has_conference(sub.conference_id):
                conf = config.get_conference(sub.conference_id)
                if conf and sub.kind in conf.deadlines:
                    deadline = conf.deadlines[sub.kind]
                    days_violation = (end_date - deadline).days
                    violations.append(DeadlineViolation(
                        submission_id=sid, 
                        submission_title=sub.title,
                        conference_id=sub.conference_id,
                        submission_type=sub.kind.value,
                        description=f"Submission {sid} completes {days_violation} days after deadline",
                        severity="high", 
                        deadline=deadline, 
                        end_date=end_date,
                        days_late=days_violation
                    ))
                else:
                    violations.append(DeadlineViolation(
                        submission_id=sid, 
                        submission_title=sub.title,
                        conference_id=sub.conference_id or "",
                        submission_type=sub.kind.value,
                        description=f"Submission {sid} has no deadline defined for type {sub.kind.value}",
                        severity="medium", 
                        deadline=date.today(), 
                        end_date=end_date,
                        days_late=0
                    ))
            else:
                violations.append(DeadlineViolation(
                    submission_id=sid, 
                    submission_title=sub.title,
                    conference_id="",
                    submission_type=sub.kind.value,
                    description=f"Submission {sid} has no conference deadline",
                    severity="medium", 
                    deadline=date.today(), 
                    end_date=end_date,
                    days_late=0
                ))
        else:
            compliant_submissions += 1
    
    # Add lead time validation violations
    abstract_lead_time_result = _validate_abstract_lead_time(schedule, config)
    paper_lead_time_result = _validate_paper_lead_time(schedule, config)
    
    # Add earliest start and engineering ready constraint violations
    earliest_start_errors = _validate_earliest_start_constraints(schedule, config)
    engineering_ready_errors = _validate_engineering_ready_constraints(schedule, config)
    
    # Convert lead time violations to DeadlineViolation objects
    for violation in abstract_lead_time_result.violations:
        sub = config.get_submission(violation.submission_id)
        violations.append(DeadlineViolation(
            submission_id=violation.submission_id,
            submission_title=sub.title if sub else violation.submission_id,
            conference_id=sub.conference_id if sub and sub.conference_id else "",
            submission_type=sub.kind.value if sub else "ABSTRACT",
            description=violation.description,
            severity=violation.severity,
            deadline=date.today(),
            end_date=date.today(),
            days_late=0 # Lead time violations don't have a direct days_late, but can be calculated if needed
        ))
    
    for violation in paper_lead_time_result.violations:
        sub = config.get_submission(violation.submission_id)
        violations.append(DeadlineViolation(
            submission_id=violation.submission_id,
            submission_title=sub.title if sub else violation.submission_id,
            conference_id=sub.conference_id if sub and sub.conference_id else "",
            submission_type=sub.kind.value if sub else "PAPER",
            description=violation.description,
            severity=violation.severity,
            deadline=date.today(),
            end_date=date.today(),
            days_late=0 # Lead time violations don't have a direct days_late, but can be calculated if needed
        ))
    
    # Convert earliest start and engineering ready violations to DeadlineViolation objects
    for error in earliest_start_errors:
        violations.append(DeadlineViolation(
            submission_id="",
            submission_title="",
            conference_id="",
            submission_type="",
            description=error,
            severity="medium",
            deadline=date.today(),
            end_date=date.today(),
            days_late=0
        ))
    
    for error in engineering_ready_errors:
        violations.append(DeadlineViolation(
            submission_id="",
            submission_title="",
            conference_id="",
            submission_type="",
            description=error,
            severity="medium",
            deadline=date.today(),
            end_date=date.today(),
            days_late=0
        ))
    
    # Update compliance count to include lead time validations
    compliant_submissions += (abstract_lead_time_result.metadata.get("compliant_submissions", 0) + 
                            paper_lead_time_result.metadata.get("compliant_submissions", 0))
    
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions meet deadlines ({compliance_rate:.1f}%)",
        metadata={
            "compliance_rate": compliance_rate, 
            "total_submissions": total_submissions, 
            "compliant_submissions": compliant_submissions
        }
    )


def _validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """Validate deadline compliance for a single submission."""
    if not sub.conference_id or not config.has_conference(sub.conference_id):
        return True
    
    conf = config.get_conference(sub.conference_id)
    if not conf or sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start_date, config)
    
    return end_date <= deadline


def _validate_abstract_lead_time(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate abstract lead time constraints."""
    violations = []
    total_abstracts = 0
    compliant_abstracts = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or sub.kind != SubmissionType.ABSTRACT:
            continue
        
        total_abstracts += 1
        end_date = sub.get_end_date(interval.start_date, config)
        
        # Check if abstract completes before paper deadline
        if sub.conference_id and config.has_conference(sub.conference_id):
            conf = config.get_conference(sub.conference_id)
            if conf and SubmissionType.PAPER in conf.deadlines:
                paper_deadline = conf.deadlines[SubmissionType.PAPER]
                if end_date > paper_deadline:
                    days_violation = (end_date - paper_deadline).days
                    violations.append(ConstraintViolation(
                        submission_id=sid, 
                        description=f"Abstract completes {days_violation} days after paper deadline",
                        severity="high"
                    ))
                else:
                    compliant_abstracts += 1
            else:
                compliant_abstracts += 1
        else:
            compliant_abstracts += 1
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{compliant_abstracts}/{total_abstracts} abstracts meet lead time constraints",
        metadata={
            "total_submissions": total_abstracts, 
            "compliant_submissions": compliant_abstracts
        }
    )


def _validate_paper_lead_time(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate paper lead time constraints."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        total_papers += 1
        end_date = sub.get_end_date(interval.start_date, config)
        
        # Check if paper completes before conference deadline
        if sub.conference_id and config.has_conference(sub.conference_id):
            conf = config.get_conference(sub.conference_id)
            if conf and sub.kind in conf.deadlines:
                deadline = conf.deadlines[sub.kind]
                if end_date > deadline:
                    days_violation = (end_date - deadline).days
                    violations.append(ConstraintViolation(
                        submission_id=sid, 
                        description=f"Paper completes {days_violation} days after deadline",
                        severity="high"
                    ))
                else:
                    compliant_papers += 1
            else:
                compliant_papers += 1
        else:
            compliant_papers += 1
    
    return ValidationResult(
        is_valid=len(violations) == 0, 
        violations=violations,
        summary=f"{compliant_papers}/{total_papers} papers meet lead time constraints",
        metadata={
            "total_submissions": total_papers, 
            "compliant_submissions": compliant_papers
        }
    )


def _validate_earliest_start_constraints(schedule: Schedule, config: Config) -> List[str]:
    """Validate that submissions respect their earliest start date constraints."""
    errors = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if submission and submission.earliest_start_date:
            if interval.start_date < submission.earliest_start_date:
                errors.append(f"Submission {submission_id} scheduled before earliest start date: "
                           f"scheduled {interval.start_date}, earliest allowed {submission.earliest_start_date}")
    
    return errors


def _validate_engineering_ready_constraints(schedule: Schedule, config: Config) -> List[str]:
    """Validate that engineering submissions respect engineering ready dates."""
    errors = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if submission and submission.engineering and submission.engineering_ready_date:
            if interval.start_date < submission.engineering_ready_date:
                errors.append(f"Engineering submission {submission_id} scheduled before engineering ready date: "
                           f"scheduled {interval.start_date}, engineering ready {submission.engineering_ready_date}")
    
    return errors


def validate_schedule(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate comprehensive schedule constraints."""
    if not schedule:
        return ValidationResult(
            is_valid=False, 
            violations=[], 
            summary="No schedule to validate",
            metadata={
                "total_submissions": 0,
                "compliant_submissions": 0
            }
        )
    
    # Import here to avoid circular imports
    from .resources import validate_resources_constraints
    from .venue import validate_venue_constraints
    
    # Validate all constraint types
    deadline_result = validate_deadline_constraints(schedule, config)
    resource_result = validate_resources_constraints(schedule, config)
    venue_result = validate_venue_constraints(schedule, config)
    
    # Combine all violations
    all_violations = (
        deadline_result.violations + 
        resource_result.violations + 
        venue_result.violations
    )
    
    # Calculate totals
    total_submissions = len(schedule.intervals)
    compliant_submissions = sum([
        deadline_result.metadata.get("compliant_submissions", 0),
        resource_result.metadata.get("compliant_submissions", 0),
        venue_result.metadata.get("compliant_submissions", 0)
    ])
    
    # Overall validation
    is_valid = len(all_violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=all_violations,
        summary=f"Schedule validation: {len(all_violations)} violations found",
        metadata={
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
    )
