"""Deadline validation functions for submission timing constraints."""

from typing import Dict, Any, List
from datetime import date, timedelta

from src.core.models import Config, Submission, DeadlineViolation, SubmissionType, Schedule, ConstraintViolation, ValidationResult
from src.core.constants import QUALITY_CONSTANTS, SCHEDULING_CONSTANTS


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
    
    # Note: Don't double-count submissions - compliant_submissions already counted in main loop
    # Lead time validations add violations but don't change compliance count
    
    return _build_validation_result(
        violations, 
        total_submissions, 
        compliant_submissions,
        "{compliant}/{total} submissions meet deadlines ({rate:.1f}%)"
    )


def _build_validation_result(violations, total_submissions, compliant_submissions, summary_template):
    """Helper to build standardized ValidationResult objects."""
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        summary=summary_template.format(
            compliant=compliant_submissions, 
            total=total_submissions, 
            rate=compliance_rate
        ),
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


def _validate_lead_time_constraints(
    schedule: Schedule, 
    config: Config, 
    submission_type: SubmissionType,
    deadline_type: SubmissionType,
    description_template: str
) -> ValidationResult:
    """Generic lead time validation for any submission type."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or sub.kind != submission_type:
            continue
        
        total_submissions += 1
        end_date = sub.get_end_date(interval.start_date, config)
        
        # Check if submission completes before deadline
        if sub.conference_id and config.has_conference(sub.conference_id):
            conf = config.get_conference(sub.conference_id)
            if conf and deadline_type in conf.deadlines:
                deadline = conf.deadlines[deadline_type]
                if end_date > deadline:
                    days_violation = (end_date - deadline).days
                    violations.append(ConstraintViolation(
                        submission_id=sid, 
                        description=description_template.format(
                            days_violation=days_violation
                        ),
                        severity="high"
                    ))
                else:
                    compliant_submissions += 1
            else:
                compliant_submissions += 1
        else:
            compliant_submissions += 1
    
    return _build_validation_result(
        violations,
        total_submissions,
        compliant_submissions,
        f"{{compliant}}/{{total}} {submission_type.value.lower()}s meet lead time constraints"
    )


def _validate_abstract_lead_time(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate abstract lead time constraints."""
    return _validate_lead_time_constraints(
        schedule, config, 
        SubmissionType.ABSTRACT, 
        SubmissionType.PAPER,
        "Abstract completes {days_violation} days after paper deadline"
    )


def _validate_paper_lead_time(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate paper lead time constraints."""
    return _validate_lead_time_constraints(
        schedule, config, 
        SubmissionType.PAPER, 
        SubmissionType.PAPER,
        "Paper completes {days_violation} days after deadline"
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






