"""Venue validation functions for conference and submission compatibility."""

from typing import Dict, Any, List
from datetime import date

from src.core.models import Config, Submission, ConferenceType, Conference, SubmissionWorkflow, Schedule, SubmissionType, ValidationResult, ConstraintViolation
from src.core.constants import QUALITY_CONSTANTS


def validate_venue_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate all venue-related constraints for the complete schedule."""
    # Run all venue validations
    conference_compat_result = _validate_conference_compatibility(schedule, config)
    conf_sub_compat_result = _validate_conference_submission_compatibility(schedule, config)
    single_conf_result = _validate_single_conference_policy(schedule, config)
    
    # Additional compatibility validation using the helper function
    compatibility_violations = []
    try:
        _validate_venue_compatibility(config.submissions, config.conferences)
    except ValueError as e:
        compatibility_violations.append(ConstraintViolation(
            submission_id="",
            description=str(e),
            severity="high"
        ))
    
    # Validate conference fields
    for conference in config.conferences:
        conference_errors = _validate_conference_fields(conference)
        for error in conference_errors:
            compatibility_violations.append(ConstraintViolation(
                submission_id="",
                description=f"Conference {conference.id}: {error}",
                severity="medium"
            ))
    
    # Combine all violations
    all_violations = (
        conference_compat_result.violations +
        conf_sub_compat_result.violations +
        single_conf_result.violations +
        compatibility_violations
    )
    
    # Determine overall validity
    is_valid = len(all_violations) == 0
    
    # Calculate overall compliance rate
    total_submissions = conference_compat_result.metadata.get("total_submissions", 0)
    compliant_submissions = conference_compat_result.metadata.get("compliant_submissions", 0)
    
    if total_submissions > 0:
        compatibility_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier)
    else:
        compatibility_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=is_valid,
        violations=all_violations,
        summary=f"Venue validation: {len(all_violations)} violations found",
        metadata={
            "compatibility_rate": compatibility_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
    )


def _validate_conference_compatibility(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate conference compatibility (medical vs engineering)."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.get_conference(sub.conference_id)
        if not conf:
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Submission {sid} references unknown conference {sub.conference_id}",
                severity="high"
            ))
            continue
        
        # Check if submission type is compatible with conference type
        if sub.kind == SubmissionType.ABSTRACT and conf.conf_type == ConferenceType.ENGINEERING:
            # Engineering conferences typically don't accept abstracts
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Abstract {sid} not compatible with engineering conference {sub.conference_id}",
                severity="medium"
            ))
            continue
        elif sub.kind == SubmissionType.PAPER and conf.conf_type == ConferenceType.MEDICAL:
            # Medical conferences typically accept both abstracts and papers
            pass
        elif sub.kind == SubmissionType.PAPER and conf.conf_type == ConferenceType.ENGINEERING:
            # Engineering conferences typically accept papers
            pass
        else:
            # Unknown combination
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Submission type {sub.kind.value} not compatible with conference type {conf.conf_type.value}",
                severity="medium"
            ))
            continue
        
        compatible_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=violations,
        summary=f"Conference compatibility: {compatible_submissions}/{total_submissions} submissions compatible ({compatibility_rate:.1f}%)",
        metadata={
            "compatibility_rate": compatibility_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compatible_submissions
        }
    )


def _validate_conference_submission_compatibility(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate that submissions are compatible with their conference submission types."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.get_conference(sub.conference_id)
        if not conf:
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Submission {sid} references unknown conference {sub.conference_id}",
                severity="high"
            ))
            continue
        
        # Check if conference accepts any of the preferred submission types
        if hasattr(sub, 'preferred_kinds') and sub.preferred_kinds is not None:
            # Check if any preferred type is accepted
            any_accepted = any(conf.accepts_submission_type(ctype) for ctype in sub.preferred_kinds)
            if not any_accepted:
                submission_type_str = conf.effective_submission_types.value
                types_str = ", ".join([t.value for t in sub.preferred_kinds])
                violations.append(ConstraintViolation(
                    submission_id=sid,
                    description=f"Submission {sid} preferred types ({types_str}) not accepted by conference {sub.conference_id} ({submission_type_str})",
                    severity="high"
                ))
                continue
        # If preferred_kinds is None, submission is open to any opportunity - skip this check
        
        compatible_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=violations,
        summary=f"Conference submission compatibility: {compatible_submissions}/{total_submissions} submissions compatible ({compatibility_rate:.1f}%)",
        metadata={
            "compatibility_rate": compatibility_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compatible_submissions
        }
    )


def _validate_single_conference_policy(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate single conference policy (no duplicate conferences per submission)."""
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    # Group submissions by conference
    conference_submissions = {}
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf_id = sub.conference_id
        
        if conf_id not in conference_submissions:
            conference_submissions[conf_id] = []
        conference_submissions[conf_id].append(sid)
    
    # Check for violations
    for conf_id, submissions in conference_submissions.items():
        if len(submissions) > 1:
            # Multiple submissions to same conference - check if this is allowed
            conf = config.get_conference(conf_id)
            if conf and conf.effective_submission_types == SubmissionWorkflow.ABSTRACT_THEN_PAPER:
                # This conference allows both abstract and paper
                abstract_count = 0
                paper_count = 0
                for sid in submissions:
                    sub = config.get_submission(sid)
                    if sub and sub.kind == SubmissionType.ABSTRACT:
                        abstract_count += 1
                    elif sub and sub.kind == SubmissionType.PAPER:
                        paper_count += 1
                
                # Check if we have both abstract and paper (which is allowed)
                if abstract_count > 0 and paper_count > 0:
                    # This is allowed for ABSTRACT_THEN_PAPER conferences
                    compliant_submissions += len(submissions)
                    continue
            
            # Multiple submissions to same conference not allowed
            violations.append(ConstraintViolation(
                submission_id=", ".join(submissions),
                description=f"Multiple submissions to same conference {conf_id}",
                severity="medium"
            ))
        else:
            compliant_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return ValidationResult(
        is_valid=is_valid,
        violations=violations,
        summary=f"Single conference policy: {compliant_submissions}/{total_submissions} submissions compliant ({compliance_rate:.1f}%)",
        metadata={
            "compatibility_rate": compliance_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
    )


def _validate_venue_compatibility(submissions: List[Submission], conferences: List[Conference]) -> None:
    """Validate that all submissions are compatible with their venues."""
    for submission in submissions:
        if submission.conference_id:
            conference = next((c for c in conferences if c.id == submission.conference_id), None)
            if not conference:
                raise ValueError(f"Submission {submission.id} references unknown conference {submission.conference_id}")
            
            if not conference.is_compatible_with_submission(submission):
                raise ValueError(f"Submission {submission.id} is not compatible with conference {submission.conference_id}")


def validate_conference_submission_compatibility(conference: Conference, submission: Submission) -> List[str]:
    """Validate that a submission is compatible with a conference."""
    errors = []
    
    # Check if submission type is accepted
    if not conference.accepts_submission_type(submission.kind):
        errors.append(f"Submission type {submission.kind.value} not accepted by this conference")
    
    # Check engineering/medical compatibility based on author
    # pccp = engineering, ed = medical
    is_engineering_submission = submission.author == "pccp"
    is_medical_submission = submission.author == "ed"
    
    if is_medical_submission and conference.conf_type == ConferenceType.ENGINEERING:
        errors.append("Medical submission not compatible with engineering conference")
    
    return errors


def _validate_conference_fields(conference: Conference) -> List[str]:
    """Validate basic conference fields and return list of errors."""
    errors = []
    if not conference.id:
        errors.append("Missing conference ID")
    if not conference.name:
        errors.append("Missing conference name")
    if not conference.deadlines:
        errors.append("No deadlines defined")
    for submission_type, deadline in conference.deadlines.items():
        if not isinstance(deadline, date):
            errors.append(f"Invalid deadline format for {submission_type}")
    return errors
