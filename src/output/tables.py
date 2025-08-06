"""Table generation for schedules."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date
from core.models import SubmissionType, Config, Submission
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


def generate_simple_monthly_table(config: Config) -> List[Dict[str, Any]]:
    """Generate monthly table for testing - simplified version."""
    rows = []
    
    # Get all conferences from config
    conferences = config.conferences
    
    # Generate rows for each conference deadline
    for conf in conferences:
        if hasattr(conf, 'deadlines') and conf.deadlines:
            for submission_type, deadline in conf.deadlines.items():
                if deadline:
                    rows.append({
                        "Month": f"{deadline.year}-{deadline.month:02d}",
                        "Deadlines": f"{conf.name} {submission_type.value}",
                        "Active Papers": ""
                    })
    
    return rows

# Legacy wrapper functions - these now delegate to the new formatters
def generate_schedule_summary_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate schedule summary table (legacy function - use output_manager instead)."""
    from .formatters.tables import format_schedule_table
    return format_schedule_table(schedule, config)

def generate_deadline_table(schedule: Dict[str, date], config: Config) -> List[Dict[str, str]]:
    """Generate deadline table (legacy function - use output_manager instead)."""
    from .formatters.tables import format_deadline_table
    return format_deadline_table(schedule, config) 