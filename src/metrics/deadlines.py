from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission, SubmissionType

def calculate_deadline_compliance(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate deadline compliance metrics."""
    if not schedule:
        return {"compliance_rate": 0.0, "missed_deadlines": 0, "total_deadlines": 0}
    
    missed_deadlines = 0
    total_deadlines = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        total_deadlines += 1
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        if end_date > deadline:
            missed_deadlines += 1
    
    compliance_rate = ((total_deadlines - missed_deadlines) / total_deadlines * 100) if total_deadlines > 0 else 0.0
    
    return {
        "compliance_rate": compliance_rate,
        "missed_deadlines": missed_deadlines,
        "total_deadlines": total_deadlines
    }

def get_deadline_violations(schedule: Dict[str, date], config: Config) -> List[Dict]:
    """Get detailed information about deadline violations."""
    violations = []
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        if end_date > deadline:
            days_late = (end_date - deadline).days
            violations.append({
                "submission_id": sid,
                "submission_title": sub.title,
                "conference_id": sub.conference_id,
                "submission_type": sub.kind.value,
                "deadline": deadline,
                "end_date": end_date,
                "days_late": days_late,
                "penalty_cost": days_late * (sub.penalty_cost_per_day or config.penalty_costs.get("default_penalty_per_day", 100.0))
            })
    
    return violations

def calculate_deadline_margins(schedule: Dict[str, date], config: Config) -> Dict[str, float]:
    """Calculate average margin before deadlines."""
    if not schedule:
        return {"avg_margin_days": 0.0, "min_margin_days": 0.0, "max_margin_days": 0.0}
    
    margins = []
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        # Calculate margin (positive if early, negative if late)
        margin = (deadline - end_date).days
        margins.append(margin)
    
    if not margins:
        return {"avg_margin_days": 0.0, "min_margin_days": 0.0, "max_margin_days": 0.0}
    
    return {
        "avg_margin_days": sum(margins) / len(margins),
        "min_margin_days": min(margins),
        "max_margin_days": max(margins)
    }

def get_deadline_risk_assessment(schedule: Dict[str, date], config: Config) -> Dict[str, List]:
    """Assess risk levels for upcoming deadlines."""
    if not schedule:
        return {"high_risk": [], "medium_risk": [], "low_risk": []}
    
    high_risk = []
    medium_risk = []
    low_risk = []
    
    current_date = min(schedule.values()) if schedule else date.today()
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        # Calculate days until deadline
        days_until_deadline = (deadline - current_date).days
        
        risk_info = {
            "submission_id": sid,
            "submission_title": sub.title,
            "conference_id": sub.conference_id,
            "submission_type": sub.kind.value,
            "deadline": deadline,
            "days_until_deadline": days_until_deadline,
            "margin_days": (deadline - end_date).days
        }
        
        # Categorize by risk level
        if days_until_deadline <= 7 or (deadline - end_date).days < 0:
            high_risk.append(risk_info)
        elif days_until_deadline <= 30:
            medium_risk.append(risk_info)
        else:
            low_risk.append(risk_info)
    
    return {
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk
    } 