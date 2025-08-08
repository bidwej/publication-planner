"""Temporal validation functions for deadlines, blackouts, and timing rules."""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from src.core.models import Config, Submission, DeadlineValidation, DeadlineViolation, SubmissionType
from src.core.constants import QUALITY_CONSTANTS, SCHEDULING_CONSTANTS
from .utilities import is_working_day


def validate_deadline_compliance(schedule: Dict[str, date], config: Config) -> DeadlineValidation:
    """Validate that all submissions meet their deadlines."""
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    if not schedule:
        return DeadlineValidation(
            is_valid=True,
            violations=[],
            summary="No submissions to validate",
            compliance_rate=perfect_compliance_rate,
            total_submissions=0,
            compliant_submissions=0
        )
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        # Skip submissions without deadlines
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        total_submissions += 1
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date using submission method
        end_date = sub.get_end_date(start_date, config)
        
        # Check if deadline is met
        if end_date <= deadline:
            compliant_submissions += 1
        else:
            days_late = (end_date - deadline).days
            violations.append(DeadlineViolation(
                submission_id=sid,
                description=f"Deadline missed by {days_late} days",
                severity="high" if days_late > 7 else "medium" if days_late > 1 else "low",
                submission_title=sub.title,
                conference_id=sub.conference_id,
                submission_type=sub.kind.value,
                deadline=deadline,
                end_date=end_date,
                days_late=days_late
            ))
    
    # Calculate compliance rate
    compliance_rate = (compliant_submissions / total_submissions * percentage_multiplier) if total_submissions > 0 else perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return DeadlineValidation(
        is_valid=is_valid,
        violations=violations,
        summary=f"{compliant_submissions}/{total_submissions} submissions meet deadlines ({compliance_rate:.1f}%)",
        compliance_rate=compliance_rate,
        total_submissions=total_submissions,
        compliant_submissions=compliant_submissions
    )


def validate_deadline_compliance_single(start_date: date, sub: Submission, config: Config) -> bool:
    """Validate deadline compliance for a single submission."""
    if not sub.conference_id or sub.conference_id not in config.conferences_dict:
        return True
    
    conf = config.conferences_dict[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start_date, config)
    
    return end_date <= deadline


def validate_deadline_with_lookahead(sub: Submission, start: date, config: Config, 
                                   conferences: Dict[str, Any], lookahead_days: int = 0) -> bool:
    """Validate deadline with lookahead for future deadlines."""
    if not sub.conference_id or sub.conference_id not in conferences:
        return True
    
    conf = conferences[sub.conference_id]
    if sub.kind not in conf.deadlines:
        return True
    
    deadline = conf.deadlines[sub.kind]
    end_date = sub.get_end_date(start, config)
    
    # Add lookahead buffer
    adjusted_deadline = deadline - timedelta(days=lookahead_days)
    
    return end_date <= adjusted_deadline


def validate_blackout_dates(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that no submissions are scheduled on blackout dates."""
    # Use constants from constants.py
    perfect_compliance_rate = QUALITY_CONSTANTS.perfect_compliance_rate
    percentage_multiplier = QUALITY_CONSTANTS.percentage_multiplier
    
    # Check if blackout periods are enabled
    if config.scheduling_options and not config.scheduling_options.get("enable_blackout_periods", True):
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": perfect_compliance_rate,
            "summary": "Blackout periods disabled"
        }
    
    if not config.blackout_dates:
        return {
            "is_valid": True,
            "violations": [],
            "compliance_rate": QUALITY_CONSTANTS.perfect_compliance_rate,
            "summary": "No blackout dates configured"
        }
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        duration_days = sub.get_duration_days(config)
        
        # Check each day of the submission
        submission_violations = []
        for i in range(duration_days + 1):
            check_date = start_date + timedelta(days=i)
            if check_date in config.blackout_dates:
                submission_violations.append(check_date)
        
        if submission_violations:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} scheduled on blackout dates: {submission_violations}",
                "severity": "medium",
                "blackout_dates": submission_violations
            })
        else:
            compliant_submissions += 1
    
    compliance_rate = (compliant_submissions / total_submissions * percentage_multiplier) if total_submissions > 0 else perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions,
        "summary": f"Blackout dates: {compliant_submissions}/{total_submissions} submissions compliant ({compliance_rate:.1f}%)"
    }


def validate_paper_lead_time_months(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate paper lead time requirements."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        total_papers += 1
        required_lead_time = config.min_paper_lead_time_days
        
        # Calculate if paper has sufficient lead time
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if SubmissionType.PAPER not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[SubmissionType.PAPER]
        end_date = sub.get_end_date(start_date, config)
        actual_lead_time = (deadline - end_date).days
        
        if actual_lead_time >= required_lead_time:
            compliant_papers += 1
        else:
            violations.append({
                "submission_id": sid,
                "description": f"Paper {sid} has insufficient lead time: {actual_lead_time} days (required: {required_lead_time})",
                "severity": "medium",
                "actual_lead_time": actual_lead_time,
                "required_lead_time": required_lead_time
            })
    
    compliance_rate = (compliant_papers / total_papers * QUALITY_CONSTANTS.percentage_multiplier) if total_papers > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compliance_rate": compliance_rate,
        "total_papers": total_papers,
        "compliant_papers": compliant_papers,
        "summary": f"Paper lead time: {compliant_papers}/{total_papers} papers compliant ({compliance_rate:.1f}%)"
    }


def _validate_early_abstract_scheduling(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate early abstract scheduling."""
    violations = []
    
    # Check if scheduling_options exists before accessing it
    if not config.scheduling_options:
        return violations
    
    abstract_advance = config.scheduling_options.get("abstract_advance_days", SCHEDULING_CONSTANTS.abstract_advance_days)
    abstracts = [sid for sid, sub in config.submissions_dict.items() 
                if sub.kind == SubmissionType.ABSTRACT]
    
    for abstract_id in abstracts:
        if abstract_id not in schedule:
            continue
        
        sub = config.submissions_dict[abstract_id]
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if SubmissionType.ABSTRACT not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[SubmissionType.ABSTRACT]
        early_date = deadline - timedelta(days=abstract_advance)
        scheduled_date = schedule[abstract_id]
        
        if scheduled_date > early_date:
            violations.append({
                "submission_id": abstract_id,
                "description": f"Abstract {abstract_id} not scheduled early enough (should be {early_date}, scheduled {scheduled_date})",
                "severity": "low"
            })
    
    return violations


def _validate_conference_response_time(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate conference response time requirements."""
    violations = []
    
    # Check if scheduling_options exists before accessing it
    if not config.scheduling_options:
        return violations
    
    response_buffer = config.scheduling_options.get("conference_response_time_days", SCHEDULING_CONSTANTS.conference_response_time_days)
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            continue
        
        # Calculate when we need to hear back
        end_date = sub.get_end_date(start_date, config)
        required_response_date = end_date - timedelta(days=response_buffer)
        
        # Check if we have enough time for response
        if required_response_date < date.today():
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} needs response by {required_response_date} but it's already past",
                "severity": "medium"
            })
    
    return violations


def _validate_working_days_only(schedule: Dict[str, date], config: Config) -> List[Dict[str, Any]]:
    """Validate working days only scheduling."""
    violations = []
    
    # Check if scheduling_options exists before accessing it
    if not config.scheduling_options or not config.scheduling_options.get("working_days_only", False):
        return violations
    
    for sid, start_date in schedule.items():
        if not is_working_day(start_date, config.blackout_dates):
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} starts on non-working day {start_date}",
                "severity": "low"
            })
    
    return violations
