"""Deadline validation functions for submission timing constraints."""

from typing import Dict, Any, List
from datetime import date, timedelta

from ..core.models import Config, Submission, DeadlineValidation, DeadlineViolation, SubmissionType, Schedule
from ..core.constants import QUALITY_CONSTANTS, SCHEDULING_CONSTANTS


def validate_deadline_constraints(schedule: Schedule, config: Config) -> DeadlineValidation:
    """Validate all deadline constraints for the complete schedule."""
    if not schedule:
        return DeadlineValidation(is_valid=True, violations=[], summary="No schedule to validate",
                                compliance_rate=QUALITY_CONSTANTS.perfect_compliance_rate, total_submissions=0, compliant_submissions=0)
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        
        # Check if submission meets its deadline
        if not _validate_deadline_compliance_single(interval.start_date, sub, config):
            end_date = sub.get_end_date(interval.start_date, config)
            if sub.conference_id and sub.conference_id in config.conferences_dict:
                conf = config.conferences_dict[sub.conference_id]
                if sub.kind in conf.deadlines:
                    deadline = conf.deadlines[sub.kind]
                    days_violation = (end_date - deadline).days
                    violations.append(DeadlineViolation(
                        submission_id=sid, description=f"Submission {sid} completes {days_violation} days after deadline",
                        days_violation=days_violation, severity="high", deadline=deadline, end_date=end_date
                    ))
                else:
                    violations.append(DeadlineViolation(
                        submission_id=sid, description=f"Submission {sid} has no deadline defined for type {sub.kind.value}",
                        days_violation=0, severity="medium", deadline=None, end_date=end_date
                    ))
            else:
                violations.append(DeadlineViolation(
                    submission_id=sid, description=f"Submission {sid} has no conference deadline",
                    days_violation=0, severity="medium", deadline=None, end_date=end_date
                ))
        else:
            compliant_submissions += 1
    
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return DeadlineValidation(
        is_valid=len(violations) == 0, violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions meet deadlines ({compliance_rate:.1f}%)",
        compliance_rate=compliance_rate, total_submissions=total_submissions, compliant_submissions=compliant_submissions
    )


def _validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """Validate deadline compliance for a single submission."""
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return True
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start_date, config)
    
    return end_date <= deadline


def _validate_abstract_lead_time(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate abstract lead time constraints."""
    violations = []
    total_abstracts = 0
    compliant_abstracts = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.ABSTRACT:
            continue
        
        total_abstracts += 1
        end_date = sub.get_end_date(interval.start_date, config)
        
        # Check if abstract completes before paper deadline
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            if SubmissionType.PAPER in conf.deadlines:
                paper_deadline = conf.deadlines[SubmissionType.PAPER]
                if end_date > paper_deadline:
                    days_violation = (end_date - paper_deadline).days
                    violations.append({
                        "submission_id": sid, "description": f"Abstract completes {days_violation} days after paper deadline",
                        "severity": "high", "days_violation": days_violation
                    })
                else:
                    compliant_abstracts += 1
            else:
                compliant_abstracts += 1
        else:
            compliant_abstracts += 1
    
    return {
        "is_valid": len(violations) == 0, "violations": violations,
        "summary": f"{compliant_abstracts}/{total_abstracts} abstracts meet lead time constraints",
        "total_abstracts": total_abstracts, "compliant_abstracts": compliant_abstracts
    }


def _validate_paper_lead_time(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Validate paper lead time constraints."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, interval in schedule.intervals.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        total_papers += 1
        end_date = sub.get_end_date(interval.start_date, config)
        
        # Check if paper completes before conference deadline
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            if sub.kind in conf.deadlines:
                deadline = conf.deadlines[sub.kind]
                if end_date > deadline:
                    days_violation = (end_date - deadline).days
                    violations.append({
                        "submission_id": sid, "description": f"Paper completes {days_violation} days after deadline",
                        "severity": "high", "days_violation": days_violation
                    })
                else:
                    compliant_papers += 1
            else:
                compliant_papers += 1
        else:
            compliant_papers += 1
    
    return {
        "is_valid": len(violations) == 0, "violations": violations,
        "summary": f"{compliant_papers}/{total_papers} papers meet lead time constraints",
        "total_papers": total_papers, "compliant_papers": compliant_papers
    }
