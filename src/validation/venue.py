"""Venue validation functions for conference compatibility and policies."""

from typing import Dict, Any
from datetime import date

from src.core.models import Config, Submission, ConferenceType
from src.core.constants import QUALITY_CONSTANTS
from src.core.models import SubmissionType


def validate_conference_compatibility(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate conference compatibility (medical vs engineering)."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} references unknown conference {sub.conference_id}",
                "severity": "high"
            })
            continue
        
        # Check if submission type is compatible with conference type
        if sub.kind == SubmissionType.ABSTRACT and conf.conf_type == ConferenceType.ENGINEERING:
            # Engineering conferences typically don't accept abstracts
            violations.append({
                "submission_id": sid,
                "description": f"Abstract {sid} not compatible with engineering conference {sub.conference_id}",
                "severity": "medium"
            })
            continue
        elif sub.kind == SubmissionType.PAPER and conf.conf_type == ConferenceType.MEDICAL:
            # Medical conferences typically accept both abstracts and papers
            pass
        elif sub.kind == SubmissionType.PAPER and conf.conf_type == ConferenceType.ENGINEERING:
            # Engineering conferences typically accept papers
            pass
        else:
            # Unknown combination
            violations.append({
                "submission_id": sid,
                "description": f"Submission type {sub.kind.value} not compatible with conference type {conf.conf_type.value}",
                "severity": "medium"
            })
            continue
        
        compatible_submissions += 1
    
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compatibility_rate": compatibility_rate,
        "total_submissions": total_submissions,
        "compatible_submissions": compatible_submissions,
        "summary": f"Conference compatibility: {compatible_submissions}/{total_submissions} submissions compatible ({compatibility_rate:.1f}%)"
    }


def validate_conference_submission_compatibility(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate that submissions are compatible with their conference submission types."""
    violations = []
    total_submissions = 0
    compatible_submissions = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id:
            continue
        
        total_submissions += 1
        conf = config.conferences_dict.get(sub.conference_id)
        if not conf:
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} references unknown conference {sub.conference_id}",
                "severity": "high"
            })
            continue
        
        # Check if conference accepts this submission type
        if not conf.accepts_submission_type(sub.kind):
            submission_type_str = conf.submission_types.value if conf.submission_types else "unknown"
            violations.append({
                "submission_id": sid,
                "description": f"Submission {sid} ({sub.kind.value}) not accepted by conference {sub.conference_id} ({submission_type_str})",
                "severity": "high",
                "submission_type": sub.kind.value,
                "conference_submission_type": submission_type_str
            })
            continue
        
        compatible_submissions += 1
    
    # Calculate compliance rate using constants from constants.py
    compatibility_rate = (compatible_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    is_valid = len(violations) == 0
    
    return {
        "is_valid": is_valid,
        "violations": violations,
        "compatibility_rate": compatibility_rate,
        "total_submissions": total_submissions,
        "compatible_submissions": compatible_submissions,
        "summary": f"Conference submission compatibility: {compatible_submissions}/{total_submissions} submissions compatible ({compatibility_rate:.1f}%)"
    }


def validate_single_conference_policy(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Validate single conference policy (one paper per conference per cycle)."""
    violations = []
    total_papers = 0
    compliant_papers = 0
    
    # Group papers by conference
    conference_papers = {}
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or sub.kind != SubmissionType.PAPER or not sub.conference_id:
            continue
        
        total_papers += 1
        conf_id = sub.conference_id
        
        if conf_id not in conference_papers:
            conference_papers[conf_id] = []
        
        conference_papers[conf_id].append({
            "submission_id": sid,
            "start_date": start_date,
            "submission": sub
        })
    
    # Check each conference for multiple papers
    for conf_id, papers in conference_papers.items():
        if len(papers) > 1:
            # Multiple papers to same conference - check if they're in different cycles
            papers.sort(key=lambda x: x["start_date"])
            
            for i in range(len(papers) - 1):
                current_paper = papers[i]
                next_paper = papers[i + 1]
                
                # Check if papers are in different annual cycles (roughly 12 months apart)
                days_between = (next_paper["start_date"] - current_paper["start_date"]).days
                
                if days_between < 365:  # Less than a year apart
                    violations.append({
                        "submission_id": next_paper["submission_id"],
                        "description": f"Multiple papers to conference {conf_id} within same cycle: {current_paper['submission_id']} and {next_paper['submission_id']}",
                        "severity": "medium",
                        "conference_id": conf_id,
                        "first_paper": current_paper["submission_id"],
                        "second_paper": next_paper["submission_id"],
                        "days_between": days_between
                    })
                else:
                    compliant_papers += 1
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
        "summary": f"Single conference policy: {compliant_papers}/{total_papers} papers compliant ({compliance_rate:.1f}%)"
    }


def validate_venue_compatibility(submissions: Dict[str, Submission], conferences: Dict[str, Any]) -> None:
    """Validate venue compatibility between submissions and conferences."""
    for sid, sub in submissions.items():
        if not sub.conference_id or sub.conference_id not in conferences:
            continue
        
        conf = conferences[sub.conference_id]
        
        # Check if conference accepts this submission type
        if not conf.accepts_submission_type(sub.kind):
            raise ValueError(f"Submission {sid} ({sub.kind.value}) not accepted by conference {sub.conference_id}")
        
        # Check if submission type is compatible with conference type
        if sub.kind == SubmissionType.ABSTRACT and conf.conf_type == ConferenceType.ENGINEERING:
            raise ValueError(f"Abstract {sid} not compatible with engineering conference {sub.conference_id}")
