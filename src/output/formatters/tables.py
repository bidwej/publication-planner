"""Table formatting utilities for output."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from ...models import Config, Submission, SubmissionType
from .dates import format_date_display, format_month_year, format_relative_time, format_duration_days

def format_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Format schedule as a table for display."""
    if not schedule:
        return []
    
    rows = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        # Calculate end date
        if sub.kind == SubmissionType.ABSTRACT:
            end_date = start_date
            duration_days = 0
        else:
            duration_days = sub.draft_window_months * 30 if sub.draft_window_months > 0 else config.min_paper_lead_time_days
            end_date = start_date + timedelta(days=duration_days)
        
        # Get conference info
        conference_name = "Unknown"
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            conference_name = conf.name
        
        # Get deadline info
        deadline_info = "No deadline"
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            if sub.kind in conf.deadlines:
                deadline = conf.deadlines[sub.kind]
                deadline_info = format_date_display(deadline)
        
        rows.append({
            "Submission": sub.title,
            "Type": sub.kind.value.title(),
            "Conference": conference_name,
            "Start Date": format_date_display(start_date),
            "End Date": format_date_display(end_date),
            "Duration": format_duration_days(duration_days),
            "Deadline": deadline_info,
            "Relative Time": format_relative_time(start_date)
        })
    
    return rows

def format_metrics_table(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Format metrics as a table for display."""
    rows = []
    
    # Schedule metrics
    rows.append({
        "Metric": "Total Submissions",
        "Value": str(metrics.get("total_submissions", 0)),
        "Description": "Number of scheduled submissions"
    })
    
    rows.append({
        "Metric": "Schedule Span",
        "Value": format_duration_days(metrics.get("schedule_span", 0)),
        "Description": "Total duration of the schedule"
    })
    
    rows.append({
        "Metric": "Makespan",
        "Value": format_duration_days(metrics.get("makespan", 0)),
        "Description": "Time from first to last submission"
    })
    
    # Quality metrics
    rows.append({
        "Metric": "Penalty Score",
        "Value": f"${metrics.get('penalty_score', 0.0):.2f}",
        "Description": "Total penalty cost for violations"
    })
    
    rows.append({
        "Metric": "Quality Score",
        "Value": f"{metrics.get('quality_score', 0.0):.3f}",
        "Description": "Overall schedule quality (0-1)"
    })
    
    rows.append({
        "Metric": "Efficiency Score",
        "Value": f"{metrics.get('efficiency_score', 0.0):.3f}",
        "Description": "Resource utilization efficiency"
    })
    
    # Compliance metrics
    rows.append({
        "Metric": "Deadline Compliance",
        "Value": f"{metrics.get('compliance_rate', 100.0):.1f}%",
        "Description": "Percentage of deadlines met"
    })
    
    rows.append({
        "Metric": "Resource Utilization",
        "Value": f"{metrics.get('resource_utilization', 0.0):.1%}",
        "Description": "Average resource utilization"
    })
    
    return rows

def format_deadline_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Format deadline compliance as a table."""
    if not schedule:
        return []
    
    rows = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        # Get conference and deadline info
        conference_name = "Unknown"
        deadline_date = None
        status = "Unknown"
        
        if sub.conference_id and sub.conference_id in config.conferences_dict:
            conf = config.conferences_dict[sub.conference_id]
            conference_name = conf.name
            
            if sub.kind in conf.deadlines:
                deadline_date = conf.deadlines[sub.kind]
                
                # Calculate end date
                if sub.kind == SubmissionType.ABSTRACT:
                    end_date = start_date
                else:
                    duration_days = sub.draft_window_months * 30 if sub.draft_window_months > 0 else config.min_paper_lead_time_days
                    end_date = start_date + timedelta(days=duration_days)
                
                # Determine status
                if end_date <= deadline_date:
                    status = "On Time"
                else:
                    days_late = (end_date - deadline_date).days
                    status = f"{days_late} days late"
        
        rows.append({
            "Submission": sub.title,
            "Conference": conference_name,
            "Type": sub.kind.value.title(),
            "Start Date": format_date_display(start_date),
            "Deadline": format_date_display(deadline_date) if deadline_date else "No deadline",
            "Status": status
        })
    
    return rows 