"""Table generation for schedules."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date, timedelta, datetime
from ..models import SubmissionType, Config, Submission
from dateutil.relativedelta import relativedelta

def generate_monthly_table(
    schedule: Dict[str, date], submissions: List[Submission], config: Config
) -> List[Dict[str, str]]:
    """Generates a monthly table showing active submissions and deadlines."""

    if not schedule:
        return []

    # Find date range
    min_date = min(schedule.values())
    max_date = max(schedule.values())

    # Extend to show completion
    max_date = max_date + relativedelta(months=3)

    rows: List[Dict[str, str]] = []
    sub_map = {s.id: s for s in submissions}

    # Generate monthly rows
    current = min_date.replace(day=1)
    while current <= max_date:
        active = []

        for sid, start_date in schedule.items():
            s = sub_map[sid]

            # Calculate end date
            if s.kind == SubmissionType.ABSTRACT:
                end_date = start_date
            else:
                duration_days = config.min_paper_lead_time_days
                end_date = start_date + relativedelta(days=duration_days)

            # Check if active in this month
            month_start = current
            month_end = current + relativedelta(months=1) - relativedelta(days=1)

            if start_date <= month_end and end_date >= month_start:
                active.append(sid)

        # Find deadlines in this month
        deadlines = []
        for conf in config.conferences:
            for kind, dl in conf.deadlines.items():
                if dl.year == current.year and dl.month == current.month:
                    deadlines.append(f"{conf.id} {kind.value} {dl.day}")

        rows.append(
            {
                "Period": current.strftime("%B %Y"),  # e.g., "January 2025"
                "Month": current.strftime("%Y-%m"),
                "Active Submissions": ", ".join(sorted(active)) if active else "None",
                "Deadlines": "; ".join(sorted(deadlines)) if deadlines else "None",
                "Count": str(len(active)),
            }
        )

        current += relativedelta(months=1)

    return rows


def generate_simple_monthly_table(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate monthly table for testing - simplified version."""
    rows = []
    
    # Get all conferences from config
    conferences = config.get("conferences", [])
    
    # Generate rows for each conference deadline
    for conf in conferences:
        if "abstract_deadline" in conf and conf["abstract_deadline"]:
            deadline_str = conf["abstract_deadline"]
            if isinstance(deadline_str, str):
                deadline = datetime.fromisoformat(deadline_str.split("T")[0])
            else:
                deadline = deadline_str
            rows.append({
                "Month": f"{deadline.year}-{deadline.month:02d}",
                "Deadlines": f"{conf['name']} Abstract",
                "Active Papers": ""
            })
        
        if "full_paper_deadline" in conf and conf["full_paper_deadline"]:
            deadline_str = conf["full_paper_deadline"]
            if isinstance(deadline_str, str):
                deadline = datetime.fromisoformat(deadline_str.split("T")[0])
            else:
                deadline = deadline_str
            rows.append({
                "Month": f"{deadline.year}-{deadline.month:02d}",
                "Deadlines": f"{conf['name']} Full Paper",
                "Active Papers": ""
            })
    
    return rows

def generate_schedule_summary_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate a summary table of the schedule."""
    if not schedule:
        return []
    
    if not hasattr(config, 'submissions_dict'):
        raise ValueError("Config must have submissions_dict attribute")
    
    rows = []
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            print(f"Warning: Submission {sid} not found in config")
            continue
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
            end_date = start_date + relativedelta(days=duration)
        else:
            end_date = start_date
        
        # Get conference info
        conf_name = "Internal"
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            conf_name = conf.id
        
        # Calculate relative time information
        today = datetime.now().date()
        days_until_start = (start_date - today).days
        weeks_until_start = days_until_start // 7 if days_until_start > 0 else 0
        months_until_start = (start_date.year - today.year) * 12 + (start_date.month - today.month)
        
        # Format relative time
        if days_until_start < 0:
            relative_time = f"Started {abs(days_until_start)} days ago"
        elif days_until_start == 0:
            relative_time = "Today"
        elif days_until_start < 7:
            relative_time = f"In {days_until_start} days"
        elif weeks_until_start < 4:
            relative_time = f"In {weeks_until_start} weeks"
        else:
            relative_time = f"In {months_until_start} months"
        
        rows.append({
            "ID": sid,
            "Title": sub.title[:50] + "..." if len(sub.title) > 50 else sub.title,
            "Type": sub.kind.value,
            "Conference": conf_name,
            "Start Date": start_date.strftime("%B %d, %Y"),  # e.g., "January 15, 2025"
            "End Date": end_date.strftime("%B %d, %Y"),
            "Duration": f"{(end_date - start_date).days + 1} days",
            "Relative Time": relative_time
        })
    
    return rows

def generate_deadline_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate a table showing deadline information."""
    if not schedule:
        return []
    
    if not hasattr(config, 'submissions_dict'):
        raise ValueError("Config must have submissions_dict attribute")
    
    rows = []
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            print(f"Warning: Submission {sid} not found in config")
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
            end_date = start_date + relativedelta(days=duration)
        else:
            end_date = start_date
        
        # Calculate margin
        margin_days = (deadline - end_date).days
        margin_status = "On Time" if margin_days >= 0 else "Late"
        
        # Calculate relative deadline information
        today = datetime.now().date()
        days_until_deadline = (deadline - today).days
        weeks_until_deadline = days_until_deadline // 7 if days_until_deadline > 0 else 0
        
        # Format relative deadline
        if days_until_deadline < 0:
            relative_deadline = f"{abs(days_until_deadline)} days ago"
        elif days_until_deadline == 0:
            relative_deadline = "Today"
        elif days_until_deadline < 7:
            relative_deadline = f"In {days_until_deadline} days"
        elif weeks_until_deadline < 4:
            relative_deadline = f"In {weeks_until_deadline} weeks"
        else:
            months_until_deadline = (deadline.year - today.year) * 12 + (deadline.month - today.month)
            relative_deadline = f"In {months_until_deadline} months"
        
        rows.append({
            "Submission": sid,
            "Title": sub.title[:40] + "..." if len(sub.title) > 40 else sub.title,
            "Conference": conf.id,
            "Deadline": deadline.strftime("%B %d, %Y"),
            "End Date": end_date.strftime("%B %d, %Y"),
            "Margin": f"{margin_days} days",
            "Status": margin_status,
            "Relative Deadline": relative_deadline
        })
    
    return rows 