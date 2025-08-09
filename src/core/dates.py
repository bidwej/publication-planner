"""Date utilities for the paper planning system."""

from typing import Optional, Dict
from datetime import date, timedelta

from src.core.models import Conference, SubmissionType



def is_working_day(check_date: date, blackout_dates: list[date] | None = None) -> bool:
    """
    Check if a date is a working day (not weekend and not blackout).
    
    Parameters
    ----------
    check_date : date
        Date to check
    blackout_dates : list[date] | None
        List of blackout dates to exclude
        
    Returns
    -------
    bool
        True if working day, False otherwise
    """
    # Check if it's a weekend (Saturday = 5, Sunday = 6)
    if check_date.weekday() >= 5:
        return False
    
    # Check if it's a blackout date
    if blackout_dates and check_date in blackout_dates:
        return False
    
    return True


def calculate_schedule_duration(schedule: Dict[str, date]) -> int:
    """
    Calculate the duration of a schedule in days.
    
    Single source of truth for schedule duration calculation to avoid
    duplicate logic across the codebase.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Dictionary mapping submission_id to start_date
        
    Returns
    -------
    int
        Duration in days from earliest to latest start date
    """
    if not schedule:
        return 0
    
    # Handle both string and date objects
    dates = []
    for date_val in schedule.values():
        if isinstance(date_val, str):
            from datetime import datetime
            dates.append(datetime.strptime(date_val, "%Y-%m-%d").date())
        else:
            dates.append(date_val)
    
    return (max(dates) - min(dates)).days if dates else 0



