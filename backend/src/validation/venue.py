"""Venue validation functions for conference compatibility and policies."""

from typing import List, Dict
from datetime import date

from ..core.models import Config, Submission, ConferenceType, Conference, SubmissionWorkflow, Schedule, SubmissionType, ValidationResult, ConstraintViolation
from ..core.constants import QUALITY_CONSTANTS


def validate_venue_constraints(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate all venue-related constraints for the complete schedule."""
    # Run all venue validations
    conference_compat_result = _validate_conference_compatibility(schedule, config)
    conf_sub_compat_result = _validate_conference_submission_compatibility(schedule, config)
    single_conf_result = _validate_single_conference_policy(schedule, config)
    
    # Additional compatibility validation using the helper function
    compatibility_violations = []
    try:
        _validate_venue_compatibility(config.submissions_dict, config.conferences_dict)
    except ValueError as e:
        compatibility_violations.append(ConstraintViolation(
            submission_id="",
            description=str(e),
            severity="high"
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


def validate_conference(conference: Conference) -> List[str]:
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


def _validate_conference_compatibility(schedule: Schedule, config: Config) -> ValidationResult:
    """Validate conference compatibility (medical vs engineering)."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
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
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            violations.append(ConstraintViolation(
                submission_id=sid,
                description=f"Submission {sid} references unknown conference {sub.conference_id}",
                severity="high"
            ))
            continue
        
        # Check if conference accepts any of the candidate submission types
        if hasattr(sub, 'candidate_kinds') and sub.candidate_kinds is not None:
            # Check if any candidate type is accepted
            any_accepted = any(conf.accepts_submission_type(ctype) for ctype in sub.candidate_kinds)
            if not any_accepted:
                submission_type_str = conf.effective_submission_types.value
                types_str = ", ".join([t.value for t in sub.candidate_kinds])
                violations.append(ConstraintViolation(
                    submission_id=sid,
                    description=f"Submission {sid} candidate types ({types_str}) not accepted by conference {sub.conference_id} ({submission_type_str})",
                    severity="high"
                ))
                continue
        # If candidate_kinds is None, submission is open to any opportunity - skip this check
        
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
        sub = config.submissions_dict.get(sid)
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
            conf = config.conferences_dict.get(conf_id)
            if conf and conf.effective_submission_types == SubmissionWorkflow.ABSTRACT_THEN_PAPER:
                # This conference allows both abstract and paper
                abstract_count = 0
                paper_count = 0
                for sid in submissions:
                    sub = config.submissions_dict.get(sid)
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


def _validate_venue_compatibility(submissions_dict: Dict[str, Submission], conferences_dict: Dict[str, Conference]) -> None:
    """Validate that all submissions are compatible with their venues."""
    for submission in submissions_dict.values():
        if submission.conference_id:
            conference = conferences_dict.get(submission.conference_id)
            if not conference:
                raise ValueError(f"Submission {submission.id} references unknown conference {submission.conference_id}")
            
            if not conference.is_compatible_with_submission(submission):
                raise ValueError(f"Submission {submission.id} is not compatible with conference {submission.conference_id}")
