"""Unified table generation and formatting for schedules."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date, timedelta
import json
import csv
from src.core.models import Config, SubmissionType, ScheduleSummary
from src.core.constants import MAX_TITLE_LENGTH, DAYS_PER_MONTH
from pathlib import Path


# ============================================================================
# Basic Table Generation Functions
# ============================================================================

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
            "Title": submission.title[:MAX_TITLE_LENGTH] + ("" if len(submission.title) > MAX_TITLE_LENGTH else ""),
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
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("" if len(sub.title) > MAX_TITLE_LENGTH else ""),
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
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("" if len(sub.title) > MAX_TITLE_LENGTH else ""),
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
            "Title": sub.title[:MAX_TITLE_LENGTH] + ("" if len(sub.title) > MAX_TITLE_LENGTH else ""),
            "Conference": conf.name,
            "Type": sub.kind.value.title(),
            "Deadline": deadline.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Status": status,
            "Days Late": str(days_diff) if status == "Late" else "0"
        })
    
    return sorted(table, key=lambda x: x["Days Late"], reverse=True)


# ============================================================================
# Advanced Formatting Functions
# ============================================================================

def format_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Format schedule as a table for display with enhanced formatting."""
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
            duration_days = sub.draft_window_months * DAYS_PER_MONTH if sub.draft_window_months > 0 else config.min_paper_lead_time_days
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
                deadline_info = _format_date_display(deadline)
        
        rows.append({
            "Submission": sub.title,
            "Type": sub.kind.value.title(),
            "Conference": conference_name,
            "Start Date": _format_date_display(start_date),
            "End Date": _format_date_display(end_date),
            "Duration": _format_duration_days(duration_days),
            "Deadline": deadline_info,
            "Relative Time": _format_relative_time(start_date)
        })
    
    return rows


def format_metrics_table(metrics: ScheduleSummary) -> List[Dict[str, str]]:
    """Format metrics as a table for display."""
    rows = []
    
    # Schedule metrics
    rows.append({
        "Metric": "Total Submissions",
        "Value": str(metrics.total_submissions),
        "Description": "Number of scheduled submissions"
    })
    
    rows.append({
        "Metric": "Schedule Span",
        "Value": _format_duration_days(metrics.schedule_span),
        "Description": "Total duration of the schedule"
    })
    
    rows.append({
        "Metric": "Schedule Span",
        "Value": _format_duration_days(metrics.schedule_span),
        "Description": "Total duration of the schedule"
    })
    
    # Quality metrics
    rows.append({
        "Metric": "Penalty Score",
        "Value": f"${metrics.penalty_score:.2f}",
        "Description": "Total penalty cost for violations"
    })
    
    rows.append({
        "Metric": "Quality Score",
        "Value": f"{metrics.quality_score:.3f}",
        "Description": "Overall schedule quality (0-1)"
    })
    
    rows.append({
        "Metric": "Efficiency Score",
        "Value": f"{metrics.efficiency_score:.3f}",
        "Description": "Resource utilization efficiency"
    })
    
    # Compliance metrics
    rows.append({
        "Metric": "Deadline Compliance",
        "Value": f"{metrics.deadline_compliance:.1f}%",
        "Description": "Percentage of deadlines met"
    })
    
    rows.append({
        "Metric": "Resource Utilization",
        "Value": f"{metrics.resource_utilization:.1%}",
        "Description": "Average resource utilization"
    })
    
    return rows


def format_deadline_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Format deadline compliance as a table with enhanced formatting."""
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
                    duration_days = sub.draft_window_months * DAYS_PER_MONTH if sub.draft_window_months > 0 else config.min_paper_lead_time_days
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
            "Start Date": _format_date_display(start_date),
            "Deadline": _format_date_display(deadline_date) if deadline_date else "No deadline",
            "Status": status
        })
    
    return rows


# ============================================================================
# Web-Specific Table Functions
# ============================================================================

def create_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Create schedule table data for web display with status tracking."""
    if not schedule:
        return []
    
    submissions_dict = config.submissions_dict
    conferences_dict = config.conferences_dict
    
    table_data = []
    
    for submission_id, start_date in schedule.items():
        submission = submissions_dict.get(submission_id)
        if not submission:
            continue
        
        # Calculate end date
        duration_days = submission.get_duration_days(config)
        end_date = start_date + timedelta(days=duration_days)
        
        # Get conference name
        conference_name = "No conference"
        if submission.conference_id:
            conference = conferences_dict.get(submission.conference_id)
            if conference:
                conference_name = conference.name
        
        # Determine status
        status = _get_submission_status(submission, start_date, end_date, config)
        
        # Create table row
        row = {
            'id': submission_id,
            'title': submission.title,
            'type': submission.kind.value.title(),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'conference': conference_name,
            'status': status,
            'duration': f"{duration_days} days",
            'engineering': "Yes" if submission.engineering else "No"
        }
        
        table_data.append(row)
    
    # Sort by start date
    table_data.sort(key=lambda x: x['start_date'])
    
    return table_data


def create_violations_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Create violations table data for web display."""
    if not validation_result:
        return []
    
    constraints = validation_result.get('constraints', {})
    violations = []
    
    # Collect all violations
    for constraint_type, constraint_data in constraints.items():
        if isinstance(constraint_data, dict) and 'violations' in constraint_data:
            for violation in constraint_data['violations']:
                violations.append({
                    'type': constraint_type.replace('_', ' ').title(),
                    'submission': violation.get('submission_id', 'Unknown'),
                    'description': violation.get('message', 'No description'),
                    'severity': violation.get('severity', 'medium'),
                    'impact': violation.get('impact', 'Unknown')
                })
    
    return violations


def create_metrics_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Create metrics table data for web display."""
    if not validation_result:
        return []  # No validation result means no data to display
    
    scores = validation_result.get('scores', {})
    summary = validation_result.get('summary', {})
    
    metrics = [
        {
            'metric': 'Penalty Score',
            'value': f"{scores.get('penalty_score', 0):.1f}",
            'status': _get_score_status(scores.get('penalty_score', 0))
        },
        {
            'metric': 'Quality Score',
            'value': f"{scores.get('quality_score', 0):.1f}",
            'status': _get_score_status(scores.get('quality_score', 0))
        },
        {
            'metric': 'Efficiency Score',
            'value': f"{scores.get('efficiency_score', 0):.1f}",
            'status': _get_score_status(scores.get('efficiency_score', 0))
        },
        {
            'metric': 'Overall Score',
            'value': f"{summary.get('overall_score', 0):.1f}",
            'status': _get_score_status(summary.get('overall_score', 0))
        }
    ]
    
    return metrics


def create_analytics_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Create analytics table data for web display."""
    if not validation_result:
        return []  # No validation result means no data to display
    
    summary = validation_result.get('summary', {})
    
    analytics = [
        {
            'category': 'Submissions',
            'metric': 'Total Submissions',
            'value': str(summary.get('total_submissions', 0))
        },
        {
            'category': 'Timeline',
            'metric': 'Duration (days)',
            'value': str(summary.get('duration_days', 0))
        },
        {
            'category': 'Compliance',
            'metric': 'Deadline Compliance',
            'value': f"{summary.get('deadline_compliance', 0):.1f}%"
        },
        {
            'category': 'Dependencies',
            'metric': 'Dependency Satisfaction',
            'value': f"{summary.get('dependency_satisfaction', 0):.1f}%"
        },
        {
            'category': 'Violations',
            'metric': 'Total Violations',
            'value': str(summary.get('total_violations', 0))
        },
        {
            'category': 'Violations',
            'metric': 'Critical Violations',
            'value': str(summary.get('critical_violations', 0))
        }
    ]
    
    return analytics


# ============================================================================
# File I/O Functions
# ============================================================================

def save_schedule_json(schedule: Dict[str, str], output_dir: str, filename: str = "schedule.json") -> str:
    """Save schedule as JSON file."""
    filepath = Path(output_dir) / filename
    with open(filepath, 'w') as f:
        json.dump(schedule, f, default=str, indent=2)
    return str(filepath)


def save_table_csv(table_data: List[Dict[str, str]], output_dir: str, filename: str) -> str:
    """Save table data as CSV file."""
    if not table_data:
        return ""
    
    filepath = Path(output_dir) / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=table_data[0].keys())
        writer.writeheader()
        writer.writerows(table_data)
    return str(filepath)


def save_metrics_json(metrics: ScheduleSummary, output_dir: str, filename: str = "metrics.json") -> str:
    """Save metrics as JSON file."""
    filepath = Path(output_dir) / filename
    with open(filepath, 'w') as f:
        json.dump(metrics, f, default=str, indent=2)
    return str(filepath)


def get_output_summary(saved_files: Dict[str, str]) -> str:
    """Generate a summary of saved output files."""
    if not saved_files:
        return "No files were saved."
    
    summary = "Output files saved:\n"
    for file_type, filepath in saved_files.items():
        if filepath:
            filename = Path(filepath).name
            summary += f"  - {filename}\n"
    
    return summary


# ============================================================================
# Helper Functions
# ============================================================================

def _format_date_display(date_obj: date) -> str:
    """Format date for display."""
    if not date_obj:
        return "N/A"
    return date_obj.strftime("%Y-%m-%d")


def _format_duration_days(days: int) -> str:
    """Format duration in days."""
    if days == 0:
        return "0 days"
    elif days == 1:
        return "1 day"
    else:
        return f"{days} days"


def _format_relative_time(target_date: date) -> str:
    """Format relative time from today."""
    from datetime import date as current_date
    today = current_date.today()
    diff = (target_date - today).days
    
    if diff < 0:
        return f"{abs(diff)} days ago"
    elif diff == 0:
        return "Today"
    elif diff == 1:
        return "Tomorrow"
    else:
        return f"In {diff} days"


def _get_submission_status(submission, start_date: date, end_date: date, config: Config) -> str:
    """Determine the status of a submission."""
    from datetime import date as current_date
    
    today = current_date.today()
    
    if today < start_date:
        return "Scheduled"
    elif start_date <= today <= end_date:
        return "Active"
    else:
        return "Completed"


def _get_score_status(score: float) -> str:
    """Get status based on score value."""
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Poor" 