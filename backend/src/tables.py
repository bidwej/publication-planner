"""Unified table generation and formatting for schedules."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date, timedelta, date as current_date
import json
import csv
from src.core.models import Config, SubmissionType, ScheduleMetrics, Schedule
from src.core.constants import DISPLAY_CONSTANTS, SCHEDULING_CONSTANTS
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
        conf_name = config.get_conference_name(submission.conference_id, default="N/A")
        
        table.append({
            "ID": submission.id,
            "Title": submission.title[:DISPLAY_CONSTANTS.max_title_length] + ("" if len(submission.title) > DISPLAY_CONSTANTS.max_title_length else ""),
            "Type": submission.kind.value.title(),
            "Conference": conf_name,
            "Engineering": "Yes" if submission.engineering else "No"
        })
    
    return table


def generate_schedule_summary_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Generate a summary table for the schedule."""
    if not schedule:
        return []
    
    table = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, interval in sorted(schedule.intervals.items(), key=lambda x: x[1].start_date):
        sub = sub_map.get(sid)
        if not sub:
            continue
            
        # Calculate end date
        duration = config.min_paper_lead_time_days if sub.kind == SubmissionType.PAPER else 0
        end_date = interval.start_date + timedelta(days=duration)
        
        # Get conference info
        conf_name = config.get_conference_name(sub.conference_id, default="N/A")
        
        table.append({
            "ID": sid,
            "Title": sub.title[:DISPLAY_CONSTANTS.max_title_length] + ("" if len(sub.title) > DISPLAY_CONSTANTS.max_title_length else ""),
            "Type": sub.kind.value.title(),
            "Conference": conf_name,
            "Start Date": interval.start_date.strftime("%Y-%m-%d"),
            "End Date": end_date.strftime("%Y-%m-%d"),
            "Duration (days)": str(duration),
            "Engineering": "Yes" if sub.engineering else "No"
        })
    
    return table


def generate_schedule_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Generate a table showing the schedule assignments."""
    if not schedule:
        return []
    
    table_data = []
    for submission_id, interval in sorted(schedule.intervals.items(), key=lambda x: x[1].start_date):
        submission = config.get_submission(submission_id)
        if submission:
            duration_days = submission.get_duration_days(config)
            end_date = interval.start_date + timedelta(days=duration_days)
            
            # Get conference info
            conference_name = config.get_conference_name(submission.conference_id, default="N/A")
            
            table_data.append({
                "ID": submission_id,
                "Title": submission.title[:50] + "..." if len(submission.title) > 50 else submission.title,
                "Type": submission.kind.value.title(),
                "Start Date": interval.start_date.strftime("%Y-%m-%d"),
                "End Date": end_date.strftime("%Y-%m-%d"),
                "Duration (days)": str(duration_days),
                "Conference": conference_name,
                "Status": "Scheduled"
            })
    
    return table_data


def generate_metrics_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Generate a table showing schedule metrics."""
    if not schedule:
        return []
    
    # Calculate metrics using intervals
    total_submissions = len(schedule.intervals)
    start_dates = [interval.start_date for interval in schedule.intervals.values()]
    end_dates = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if submission:
            duration_days = submission.get_duration_days(config)
            end_date = interval.start_date + timedelta(days=duration_days)
            end_dates.append(end_date)
    
    if not end_dates:
        return []
    
    earliest_start = min(start_dates)
    latest_end = max(end_dates)
    schedule_span = (latest_end - earliest_start).days
    
    # Calculate deadline compliance
    deadline_violations = 0
    total_with_deadlines = 0
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if submission and submission.conference_id:
            conference = config.get_conference(submission.conference_id)
            if conference and submission.kind in conference.deadlines:
                total_with_deadlines += 1
                deadline = conference.deadlines[submission.kind]
                duration_days = submission.get_duration_days(config)
                end_date = interval.start_date + timedelta(days=duration_days)
                if end_date > deadline:
                    deadline_violations += 1
    
    compliance_rate = (1.0 - (deadline_violations / total_with_deadlines)) * 100 if total_with_deadlines > 0 else 100.0
    
    table_data = [
        {"Metric": "Total Submissions", "Value": str(total_submissions)},
        {"Metric": "Schedule Span (days)", "Value": str(schedule_span)},
        {"Metric": "Earliest Start", "Value": earliest_start.strftime("%Y-%m-%d")},
        {"Metric": "Latest End", "Value": latest_end.strftime("%Y-%m-%d")},
        {"Metric": "Deadline Compliance", "Value": f"{compliance_rate:.1f}%"},
        {"Metric": "Violations", "Value": str(deadline_violations)},
        {"Metric": "Max Concurrent", "Value": str(config.max_concurrent_submissions)}
    ]
    
    return table_data


def generate_deadline_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Generate a table showing deadline information."""
    if not schedule:
        return []
    
    table_data = []
    for submission_id, interval in sorted(schedule.intervals.items(), key=lambda x: x[1].start_date):
        submission = config.get_submission(submission_id)
        if submission and submission.conference_id:
            conference = config.get_conference(submission.conference_id)
            if conference and submission.kind in conference.deadlines:
                deadline = conference.deadlines[submission.kind]
                duration_days = submission.get_duration_days(config)
                end_date = interval.start_date + timedelta(days=duration_days)
                days_until_deadline = (deadline - end_date).days
                status = "On Time" if days_until_deadline >= 0 else "Late"
                
                table_data.append({
                    "Submission": submission_id,
                    "Conference": conference.name,
                    "Type": submission.kind.value.title(),
                    "Start Date": interval.start_date.strftime("%Y-%m-%d"),
                    "End Date": end_date.strftime("%Y-%m-%d"),
                    "Deadline": deadline.strftime("%Y-%m-%d"),
                    "Days Until Deadline": str(days_until_deadline),
                    "Status": status
                })
    
    return table_data


def generate_violations_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate a table showing constraint violations."""
    if not validation_result or "constraints" not in validation_result:
        return []
    
    table_data = []
    constraints = validation_result["constraints"]
    
    # Process deadline violations
    if "deadlines" in constraints:
        for violation in constraints["deadlines"].get("violations", []):
            table_data.append({
                "Type": "Deadline",
                "Submission": violation.get("submission_id", "Unknown"),
                "Description": violation.get("description", "Unknown"),
                "Severity": violation.get("severity", "medium"),
                "Days Late": str(violation.get("days_late", 0))
            })
    
    # Process dependency violations
    if "dependencies" in constraints:
        for violation in constraints["dependencies"].get("violations", []):
            table_data.append({
                "Type": "Dependency",
                "Submission": violation.get("submission_id", "Unknown"),
                "Description": violation.get("description", "Unknown"),
                "Severity": violation.get("severity", "medium"),
                "Dependency": violation.get("dependency_id", "Unknown")
            })
    
    # Process resource violations
    if "resources" in constraints:
        for violation in constraints["resources"].get("violations", []):
            table_data.append({
                "Type": "Resource",
                "Submission": violation.get("submission_id", "Unknown"),
                "Description": violation.get("description", "Unknown"),
                "Severity": violation.get("severity", "medium"),
                "Load": str(violation.get("load", 0)),
                "Limit": str(violation.get("limit", 0))
            })
    
    return table_data


def generate_penalties_table(penalty_breakdown: Dict[str, float]) -> List[Dict[str, str]]:
    """Generate a table showing penalty breakdown."""
    if not penalty_breakdown:
        return []
    
    table_data = []
    for penalty_type, amount in penalty_breakdown.items():
        if amount > 0:  # Only show non-zero penalties
            table_data.append({
                "Penalty Type": penalty_type.replace("_", " ").title(),
                "Amount": f"${amount:,.2f}",
                "Percentage": f"{(amount / penalty_breakdown.get('total_penalty', 1)) * 100:.1f}%"
            })
    
    return table_data


# ============================================================================
# Advanced Formatting Functions
# ============================================================================

def format_schedule_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Format schedule as a table for display with enhanced formatting."""
    if not schedule:
        return []
    
    rows = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, interval in schedule.intervals.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        # Calculate end date
        # Fixed time constants
        days_per_month = SCHEDULING_CONSTANTS.days_per_month
        
        if sub.kind == SubmissionType.ABSTRACT:
            end_date = interval.start_date
            duration_days = 0
        else:
            duration_days = sub.draft_window_months * days_per_month if sub.draft_window_months > 0 else config.min_paper_lead_time_days
            end_date = interval.start_date + timedelta(days=duration_days)
        
        # Get conference info
        conference_name = config.get_conference_name(sub.conference_id, default="Unknown")
        
        # Get deadline info
        deadline_info = "No deadline"
        deadline = config.get_deadline_for(sub)
        if deadline:
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


def format_metrics_table(metrics: ScheduleMetrics) -> List[Dict[str, str]]:
    """Format metrics as a table for display."""
    rows = []
    
    # Schedule metrics
    rows.append({
        "Metric": "Total Submissions",
        "Value": str(metrics.submission_count),
        "Description": "Number of total submissions"
    })
    
    rows.append({
        "Metric": "Scheduled Submissions",
        "Value": str(metrics.scheduled_count),
        "Description": "Number of scheduled submissions"
    })
    
    rows.append({
        "Metric": "Schedule Duration",
        "Value": _format_duration_days(metrics.duration_days),
        "Description": "Total duration of the schedule in days"
    })
    
    # Quality metrics
    rows.append({
        "Metric": "Total Penalty",
        "Value": f"${metrics.total_penalty:.2f}",
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
        "Metric": "Compliance Rate",
        "Value": f"{metrics.compliance_rate:.1f}%",
        "Description": "Percentage of constraints satisfied"
    })
    
    rows.append({
        "Metric": "Resource Utilization",
        "Value": f"{metrics.utilization_rate:.1f}%",
        "Description": "Average resource utilization"
    })
    
    return rows


def format_deadline_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Format deadline compliance as a table with enhanced formatting."""
    if not schedule:
        return []
    
    rows = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, interval in schedule.intervals.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        # Get conference and deadline info
        conference_name = config.get_conference_name(sub.conference_id, default="Unknown")
        deadline_date = None
        status = "Unknown"
        
        if deadline_date:
            # Calculate end date
            # Fixed time constants
            days_per_month = SCHEDULING_CONSTANTS.days_per_month
            
            if sub.kind == SubmissionType.ABSTRACT:
                end_date = interval.start_date
            else:
                duration_days = sub.draft_window_months * days_per_month if sub.draft_window_months > 0 else config.min_paper_lead_time_days
                end_date = interval.start_date + timedelta(days=duration_days)
            
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

def create_schedule_table(schedule: Schedule, config: Config) -> List[Dict[str, str]]:
    """Create schedule table data for web display with status tracking."""
    if not schedule:
        return []
    
    # Use the config methods instead of dict access
    
    table_data = []
    
    for submission_id, interval in schedule.intervals.items():
        submission = config.get_submission(submission_id)
        if not submission:
            continue
        
        # Calculate end date
        duration_days = submission.get_duration_days(config)
        end_date = interval.start_date + timedelta(days=duration_days)
        
        # Get conference name
        conference_name = "No conference"
        if submission.conference_id:
            conference = config.get_conference(submission.conference_id)
            if conference:
                conference_name = conference.name
        
        # Determine status
        status = _get_submission_status(submission, interval.start_date, end_date, config)
        
        # Create table row
        row = {
            'id': submission_id,
            'title': submission.title,
            'type': submission.kind.value.title(),
            'start_date': interval.start_date.strftime('%Y-%m-%d'),
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

def save_schedule_json(schedule: Schedule, output_dir: str, filename: str = "schedule.json") -> str:
    """Save schedule as JSON file."""
    filepath = Path(output_dir) / filename
    with open(filepath, 'w', encoding='utf-8') as f:
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


def save_metrics_json(metrics: ScheduleMetrics, output_dir: str, filename: str = "metrics.json") -> str:
    """Save metrics as JSON file."""
    filepath = Path(output_dir) / filename
    with open(filepath, 'w', encoding='utf-8') as f:
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
