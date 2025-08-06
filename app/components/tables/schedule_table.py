"""
Schedule table component for displaying schedule data.
"""

from typing import Dict, List, Any
from datetime import date, timedelta
from core.models import Config, Submission, SubmissionType

def create_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """
    Create schedule table data for display.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Schedule mapping submission_id to start_date
    config : Config
        Configuration containing submission data
        
    Returns
    -------
    List[Dict[str, str]]
        Table data for DataTable component
    """
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
        status = get_submission_status(submission, start_date, end_date, config)
        
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

def get_submission_status(submission: Submission, start_date: date, end_date: date, config: Config) -> str:
    """Determine the status of a submission."""
    from datetime import date as current_date
    
    today = current_date.today()
    
    if today < start_date:
        return "Scheduled"
    elif start_date <= today <= end_date:
        return "Active"
    else:
        return "Completed"

def create_violations_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Create violations table data for display.
    
    Parameters
    ----------
    validation_result : Dict[str, Any]
        Validation results containing violations
        
    Returns
    -------
    List[Dict[str, str]]
        Table data for violations DataTable
    """
    if not validation_result:
        return []
    
    constraints = validation_result.get("constraints", {})
    table_data = []
    
    # Process deadline violations
    deadline_violations = constraints.get("deadlines", {}).get("violations", [])
    for violation in deadline_violations:
        table_data.append({
            'submission': violation.get('submission_id', 'Unknown'),
            'type': 'Deadline',
            'description': violation.get('description', 'Unknown violation'),
            'severity': violation.get('severity', 'medium'),
            'impact': f"{violation.get('days_late', 0)} days late"
        })
    
    # Process dependency violations
    dependency_violations = constraints.get("dependencies", {}).get("violations", [])
    for violation in dependency_violations:
        table_data.append({
            'submission': violation.get('submission_id', 'Unknown'),
            'type': 'Dependency',
            'description': violation.get('description', 'Unknown violation'),
            'severity': violation.get('severity', 'medium'),
            'impact': f"{violation.get('days_violation', 0)} days violation"
        })
    
    # Process resource violations
    resource_violations = constraints.get("resources", {}).get("violations", [])
    for violation in resource_violations:
        table_data.append({
            'submission': violation.get('submission_id', 'Unknown'),
            'type': 'Resource',
            'description': violation.get('description', 'Unknown violation'),
            'severity': violation.get('severity', 'medium'),
            'impact': f"{violation.get('excess', 0)} excess submissions"
        })
    
    # Process conference compatibility violations
    conference_violations = constraints.get("conference_compatibility", {}).get("violations", [])
    for violation in conference_violations:
        table_data.append({
            'submission': violation.get('submission_id', 'Unknown'),
            'type': 'Conference',
            'description': violation.get('description', 'Unknown violation'),
            'severity': violation.get('severity', 'medium'),
            'impact': 'Venue mismatch'
        })
    
    return table_data

def create_metrics_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Create metrics table data for display.
    
    Parameters
    ----------
    validation_result : Dict[str, Any]
        Validation and scoring results
        
    Returns
    -------
    List[Dict[str, str]]
        Table data for metrics DataTable
    """
    if not validation_result:
        return []
    
    summary = validation_result.get("summary", {})
    constraints = validation_result.get("constraints", {})
    
    table_data = [
        {
            'metric': 'Overall Score',
            'value': f"{summary.get('overall_score', 0):.1f}/100",
            'status': get_score_status(summary.get('overall_score', 0))
        },
        {
            'metric': 'Deadline Compliance',
            'value': f"{summary.get('deadline_compliance', 0):.1f}%",
            'status': get_score_status(summary.get('deadline_compliance', 0))
        },
        {
            'metric': 'Dependency Satisfaction',
            'value': f"{summary.get('dependency_satisfaction', 0):.1f}%",
            'status': get_score_status(summary.get('dependency_satisfaction', 0))
        },
        {
            'metric': 'Resource Utilization',
            'value': f"{summary.get('resource_valid', False) and 'Valid' or 'Invalid'}",
            'status': 'success' if summary.get('resource_valid', False) else 'danger'
        },
        {
            'metric': 'Timeline Duration',
            'value': f"{summary.get('duration_days', 0)} days",
            'status': 'info'
        },
        {
            'metric': 'Peak Load',
            'value': f"{summary.get('peak_load', 0)} submissions",
            'status': 'info'
        },
        {
            'metric': 'Total Violations',
            'value': f"{validation_result.get('total_violations', 0)}",
            'status': 'danger' if validation_result.get('total_violations', 0) > 0 else 'success'
        }
    ]
    
    return table_data

def get_score_status(score: float) -> str:
    """Get status color for a score."""
    if score >= 90:
        return 'success'
    elif score >= 70:
        return 'warning'
    else:
        return 'danger'

def create_analytics_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Create analytics table data for display.
    
    Parameters
    ----------
    validation_result : Dict[str, Any]
        Validation and analytics results
        
    Returns
    -------
    List[Dict[str, str]]
        Table data for analytics DataTable
    """
    if not validation_result:
        return []
    
    analytics = validation_result.get("analytics", {})
    
    table_data = [
        {
            'category': 'Schedule Completeness',
            'metric': 'Completion Rate',
            'value': f"{analytics.get('completion_rate', 0):.1f}%",
            'description': 'Percentage of submissions scheduled'
        },
        {
            'category': 'Timeline Analysis',
            'metric': 'Duration',
            'value': f"{analytics.get('duration_days', 0)} days",
            'description': 'Total schedule duration'
        },
        {
            'category': 'Resource Analysis',
            'metric': 'Peak Load',
            'value': f"{analytics.get('peak_load', 0)}",
            'description': 'Maximum concurrent submissions'
        },
        {
            'category': 'Quality Analysis',
            'metric': 'Overall Quality',
            'value': f"{analytics.get('overall_score', 0):.1f}/100",
            'description': 'Overall schedule quality score'
        }
    ]
    
    return table_data
