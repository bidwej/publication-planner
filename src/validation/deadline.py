"""Deadline validation functions for submissions."""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from src.core.models import Config, Submission, DeadlineValidation, DeadlineViolation, SubmissionType
from src.core.constants import QUALITY_CONSTANTS, SCHEDULING_CONSTANTS


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
    
    # Perform all validation checks
    deadline_violations = _validate_deadline_violations(schedule, config)
    blackout_violations = _validate_blackout_dates(schedule, config)
    lead_time_violations = _validate_paper_lead_time_months(schedule, config)
    
    # Combine all violations
    all_violations = []
    all_violations.extend(deadline_violations)
    all_violations.extend(blackout_violations.get("violations", []))
    all_violations.extend(lead_time_violations.get("violations", []))
    
    # Calculate overall statistics
    total_submissions = len(schedule)
    compliant_submissions = total_submissions - len(all_violations)
    
    # Calculate compliance rate
    compliance_rate = (compliant_submissions / total_submissions * percentage_multiplier) if total_submissions > 0 else perfect_compliance_rate
    is_valid = len(all_violations) == 0
    
    # Create summary
    summary_parts = []
    if deadline_violations:
        summary_parts.append(f"{len(deadline_violations)} deadline violations")
    if blackout_violations.get("violations"):
        summary_parts.append(f"{len(blackout_violations['violations'])} blackout violations")
    if lead_time_violations.get("violations"):
        summary_parts.append(f"{len(lead_time_violations['violations'])} lead time violations")
    
    summary = f"{compliant_submissions}/{total_submissions} submissions compliant"
    if summary_parts:
        summary += f" ({', '.join(summary_parts)})"
    
    return DeadlineValidation(
        is_valid=is_valid,
        violations=all_violations,
        summary=summary,
        compliance_rate=compliance_rate,
        total_submissions=total_submissions,
        compliant_submissions=compliant_submissions
    )


def _validate_deadline_violations(schedule: Dict[str, date], config: Config) -> List[DeadlineViolation]:
    """Validate deadline compliance and return violations."""
    violations = []
    
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
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date using submission method
        end_date = sub.get_end_date(start_date, config)
        
        # Check if deadline is met
        if end_date > deadline:
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
    
    return violations


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


def _validate_deadline_with_lookahead(sub: Submission, start: date, config: Config, 
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


def _validate_blackout_dates(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that no submissions are scheduled on blackout dates."""
    if not config.blackout_dates:
        return {
            "is_valid": True,
            "violations": [],
            "summary": "No blackout dates configured",
            "total_submissions": 0,
            "compliant_submissions": 0
        }
    
    violations = []
    total_submissions = 0
    compliant_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        total_submissions += 1
        
        # Check if start date is on a blackout date
        if start_date in config.blackout_dates:
            violations.append({
                "submission_id": sid,
                "description": f"Submission scheduled on blackout date {start_date}",
                "severity": "high",
                "blackout_date": start_date
            })
        else:
            compliant_submissions += 1
    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"{compliant_submissions}/{total_submissions} submissions avoid blackout dates",
        "total_submissions": total_submissions,
        "compliant_submissions": compliant_submissions
    }


def _validate_paper_lead_time_months(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that papers have sufficient lead time before deadlines."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if SubmissionType.PAPER not in conf.deadlines:
            continue
        
        total_papers += 1
        deadline = conf.deadlines[SubmissionType.PAPER]
        end_date = sub.get_end_date(start_date, config)
        
        # Calculate lead time in months
        lead_time_days = (deadline - end_date).days
        lead_time_months = lead_time_days / 30.44  # Average days per month
        
        min_lead_time_months = config.min_paper_lead_time_days / 30.44  # Convert days to months
        
        if lead_time_months < min_lead_time_months:
            violations.append({
                "submission_id": sid,
                "description": f"Paper has only {lead_time_months:.1f} months lead time (minimum {min_lead_time_months})",
                "severity": "medium",
                "lead_time_months": lead_time_months,
                "min_required": min_lead_time_months
            })
        else:
            compliant_papers += 1
    
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "summary": f"{compliant_papers}/{total_papers} papers meet lead time requirements",
        "total_papers": total_papers,
        "compliant_papers": compliant_papers
    }
