"""
Timeline calculations and activity positioning for Gantt charts.
Handles timeline range, date calculations, and activity row assignments.
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional, List

from src.core.models import Config
from src.validation.resources import validate_resources_constraints
from src.core.models import Submission


def get_timeline_range(schedule: Optional[Dict[str, date]], config: Config) -> Dict[str, Any]:
    """Get timeline range and chart display settings."""
    if not schedule:
        # Default chart dimensions if no schedule
        default_start = date.today()
        default_end = default_start + timedelta(days=365)
        return {
            'min_date': default_start,
            'max_date': default_end,
            'timeline_start': default_start,
            'span_days': 365,
            'max_concurrency': 0
        }
    
    # Calculate natural timeline from schedule
    min_date = min(schedule.values())
    max_date = max(schedule.values())
    
    # Add buffer for better visualization
    buffer_days = 30
    timeline_start = min_date - timedelta(days=buffer_days)
    timeline_end = max_date + timedelta(days=buffer_days)
    
    # Calculate span
    span_days = (timeline_end - timeline_start).days
    
    # Get max concurrency from business logic
    resource_validation = validate_resources_constraints(schedule, config)
    max_concurrency = resource_validation.max_observed
    
    return {
        'min_date': timeline_start,
        'max_date': timeline_end,
        'timeline_start': timeline_start,
        'span_days': span_days,
        'max_concurrency': max_concurrency
    }





def assign_activity_rows(schedule: Optional[Dict[str, date]], config: Config) -> Dict[str, int]:
    """Assign each activity to a specific row for visual layout."""
    if not schedule:
        return {}
    
    # Get submission objects to calculate durations
    submissions = {sub.id: sub for sub in config.submissions}
    
    # Group submissions by their dependency chains (treat dependent tasks as one unit)
    dependency_groups = _group_by_dependencies(schedule, submissions)
    
    # Calculate time intervals for each dependency group (not individual submissions)
    group_intervals = []
    for group_id, group_submissions in dependency_groups.items():
        # Find the earliest start and latest end for the entire group
        group_start = min(schedule[sub_id] for sub_id in group_submissions)
        group_end = max(
            schedule[sub_id] + timedelta(days=submissions[sub_id].get_duration_days(config)) 
            for sub_id in group_submissions
        )
        group_intervals.append((group_id, group_start, group_end, group_submissions))
    
    # Sort by start date
    group_intervals.sort(key=lambda x: x[1])
    
    # Assign rows based on actual overlaps between dependency groups
    concurrency_map = {}
    used_rows = []  # Track which rows are occupied and until when
    
    for group_id, start_date, end_date, group_submissions in group_intervals:
        # Find the first available row
        row = 0
        while row < len(used_rows):
            if used_rows[row] <= start_date:
                # This row is free
                break
            row += 1
        
        # If no free row found, create a new one
        if row >= len(used_rows):
            used_rows.append(end_date)
        else:
            # Update the row's end time
            used_rows[row] = end_date
        
        # Assign all submissions in this group to the same row
        for submission_id in group_submissions:
            concurrency_map[submission_id] = row
    
    return concurrency_map





def _group_by_dependencies(schedule: Dict[str, date], submissions: Dict[str, Submission]) -> Dict[str, List[str]]:
    """Group submissions by their dependency relationships."""
    groups = {}
    processed = set()
    
    for submission_id in schedule.keys():
        if submission_id in processed:
            continue
            
        # Start a new group
        group_id = f"group_{len(groups)}"
        group_submissions = []
        
        # Find all submissions in this dependency chain
        _collect_dependency_chain(submission_id, schedule, submissions, group_submissions, processed)
        
        groups[group_id] = group_submissions
    
    return groups


def _collect_dependency_chain(submission_id: str, schedule: Dict[str, date], 
                            submissions: Dict[str, Submission], group: List[str], processed: set):
    """Recursively collect all submissions in a dependency chain."""
    if submission_id in processed or submission_id not in schedule:
        return
    
    processed.add(submission_id)
    group.append(submission_id)
    
    submission = submissions.get(submission_id)
    if submission and submission.depends_on:
        # Add dependencies first (they come before this submission)
        for dep_id in submission.depends_on:
            if dep_id in schedule:
                _collect_dependency_chain(dep_id, schedule, submissions, group, processed)
    
    # Find submissions that depend on this one
    for other_id, other_submission in submissions.items():
        if (other_id in schedule and other_submission.depends_on and 
            submission_id in other_submission.depends_on):
            _collect_dependency_chain(other_id, schedule, submissions, group, processed)



