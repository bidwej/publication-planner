"""
Schedule table component for displaying schedule data.
"""

from typing import Dict, List, Any
from datetime import date, timedelta
from core.models import Config, Submission, SubmissionType

def create_schedule_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Create schedule table data for display."""
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

def _get_submission_status(submission: Submission, start_date: date, end_date: date, config: Config) -> str:
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
    """Create violations table data for display."""
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
    """Create metrics table data for display."""
    if not validation_result:
        return []
    
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

def create_analytics_table(validation_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Create analytics table data for display."""
    if not validation_result:
        return []
    
    summary = validation_result.get('summary', {})
    constraints = validation_result.get('constraints', {})
    
    analytics = [
        {
            'category': 'Schedule Overview',
            'metric': 'Total Submissions',
            'value': str(summary.get('total_submissions', 0))
        },
        {
            'category': 'Schedule Overview',
            'metric': 'Schedule Duration',
            'value': f"{summary.get('duration_days', 0)} days"
        },
        {
            'category': 'Compliance',
            'metric': 'Deadline Compliance',
            'value': f"{summary.get('deadline_compliance', 0):.1f}%"
        },
        {
            'category': 'Compliance',
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
