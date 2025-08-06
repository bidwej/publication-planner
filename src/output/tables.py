"""Unified table generation for schedules."""

from typing import Dict, List, Any
from datetime import date, timedelta
from core.models import Config, SubmissionType
from core.constants import MAX_TITLE_LENGTH


def generate_simple_monthly_table(config: Config) -> List[Dict[str, Any]]:
    """Generate a simple monthly table for the configuration."""
    if not config.submissions:
        return []
    
    table = []
    for submission in config.submissions:
        # Get conference info
        conf_name = "N/A"
        if submission.conference_id and submission.conference_id in config.conferences_dict:
            conf_name = config.conferences_dict[submission.conference_id].name
        
        table.append({
            "ID": submission.id,
            "Title": submission.title[:MAX_TITLE_LENGTH] + ("..." if len(submission.title) > MAX_TITLE_LENGTH else ""),
            "Type": submission.kind.value.title(),
            "Conference": conf_name,
            "Engineering": "Yes" if submission.engineering else "No"
        })
    
    return table


def generate_schedule_summary_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate a summary table for the schedule."""
    if not schedule:
        return []
    
    table = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in sorted(schedule.items(), key=lambda x: x[1]):
        sub = sub_map.get(sid)
        if not sub:
            continue
            
        # Calculate end date
        duration = config.min_paper_lead_time_days if sub.kind == SubmissionType.PAPER else 0
        end_date = start_date + timedelta(days=duration)
        
        # Get conference info
        conf_name = "N/A"
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf_name = config.conferences_dict[sub.conference_id].name
        
        table.append({
            "ID": sid,
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("..." if len(sub.title) > MAX_TITLE_LENGTH else ""),
            "Type": sub.kind.value.title(),
            "Conference": conf_name,
            "Start Date": start_date.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Duration (days)": str(duration),
            "Engineering": "Yes" if sub.engineering else "No"
        })
    
    return table


def generate_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate a comprehensive schedule table."""
    if not schedule:
        return []
    
    table = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in sorted(schedule.items(), key=lambda x: x[1]):
        sub = sub_map.get(sid)
        if not sub:
            continue
            
        # Calculate end date
        duration = config.min_paper_lead_time_days if sub.kind == SubmissionType.PAPER else 0
        end_date = start_date + timedelta(days=duration)
        
        # Get conference info
        conf_name = "N/A"
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf_name = config.conferences_dict[sub.conference_id].name
        
        table.append({
            "ID": sid,
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("..." if len(sub.title) > MAX_TITLE_LENGTH else ""),
            "Type": sub.kind.value.title(),
            "Conference": conf_name,
            "Start Date": start_date.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Duration (days)": str(duration),
            "Engineering": "Yes" if sub.engineering else "No"
        })
    
    return table


def generate_metrics_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate metrics summary table."""
    if not schedule:
        return []
    
    # Calculate basic metrics
    total_submissions = len(schedule)
    abstracts = papers = 0
    sub_map = {s.id: s for s in config.submissions}
    
    for sid in schedule:
        sub = sub_map.get(sid)
        if sub:
            if sub.kind == SubmissionType.ABSTRACT:
                abstracts += 1
            elif sub.kind == SubmissionType.PAPER:
                papers += 1
    
    # Calculate date range
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    duration = (end_date - start_date).days
    
    return [
        {"Metric": "Total Submissions", "Value": str(total_submissions)},
        {"Metric": "Abstracts", "Value": str(abstracts)},
        {"Metric": "Papers", "Value": str(papers)},
        {"Metric": "Start Date", "Value": start_date.strftime("%Y-%m-%d")},
        {"Metric": "End Date", "Value": end_date.strftime("%Y-%m-%d")},
        {"Metric": "Duration (days)", "Value": str(duration)},
        {"Metric": "Avg Submissions/Day", "Value": f"{total_submissions/duration:.2f}" if duration > 0 else "N/A"}
    ]


def generate_deadline_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate deadline compliance table."""
    if not schedule:
        return []
    
    table = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub or not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        duration = config.min_paper_lead_time_days if sub.kind == SubmissionType.PAPER else 0
        end_date = start_date + timedelta(days=duration)
        
        status = "On Time" if end_date <= deadline else "Late"
        days_diff = (end_date - deadline).days if end_date > deadline else 0
        
        table.append({
            "Submission": sid,
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("..." if len(sub.title) > MAX_TITLE_LENGTH else ""),
            "Conference": conf.name,
            "Type": sub.kind.value.title(),
            "Deadline": deadline.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Status": status,
            "Days Late": str(days_diff) if status == "Late" else "0"
        })
    
    return sorted(table, key=lambda x: x["Days Late"], reverse=True) 