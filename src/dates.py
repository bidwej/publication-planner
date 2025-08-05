"""Date parsing and utility functions for the paper planner system."""

from datetime import date, datetime
from typing import Optional, Union
from dateutil.relativedelta import relativedelta


def parse_date_safe(date_str: Optional[Union[str, date]], default: Optional[date] = None) -> Optional[date]:
    """
    Parse a date string safely, returning default value on error.

    Args:
        date_str: Date string in YYYY-MM-DD format, or None, or already a date object
        default: Default value to return if parsing fails

    Returns:
        Parsed date object, default value, or None
    """
    if date_str is None:
        return None

    if isinstance(date_str, date):
        return date_str

    if not isinstance(date_str, str):
        return default

    # Clean the string (remove time component if present)
    clean = date_str.split("T")[0]

    try:
        return datetime.fromisoformat(clean).date()
    except ValueError:
        return default


def add_working_days(start_date: date, duration_days: int, blackout_dates: Optional[list[date]] = None) -> date:
    """
    Add working days to a date, skipping weekends and blackout dates.
    
    Args:
        start_date: Starting date
        duration_days: Number of working days to add
        blackout_dates: List of dates to skip (weekends, holidays, etc.)
        
    Returns:
        End date after adding working days
    """
    if blackout_dates is None:
        blackout_dates = []
    
    current = start_date
    days_added = 0
    
    while days_added < duration_days:
        current += relativedelta(days=1)
        if is_working_day(current, blackout_dates):
            days_added += 1
    
    return current


def is_working_day(check_date: date, blackout_dates: Optional[list[date]] = None) -> bool:
    """
    Check if a date is a working day (not weekend or blackout).
    
    Args:
        check_date: Date to check
        blackout_dates: List of blackout dates (weekends, holidays, etc.)
        
    Returns:
        True if it's a working day, False otherwise
    """
    if blackout_dates is None:
        blackout_dates = []
    
    # Check if it's a weekend
    if check_date.weekday() in [5, 6]:  # Saturday, Sunday
        return False
    
    # Check if it's in the blackout dates
    if check_date in blackout_dates:
        return False
    
    return True


def days_between(start_date: date, end_date: date) -> int:
    """
    Calculate the number of days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of days between the dates
    """
    return (end_date - start_date).days


def months_between(start_date: date, end_date: date) -> int:
    """
    Calculate the number of months between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of months between the dates
    """
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


def format_date_for_display(date_obj: Optional[date]) -> str:
    """
    Format a date object for display.
    
    Args:
        date_obj: Date object to format
        
    Returns:
        Formatted date string (YYYY-MM-DD) or "None" if input is None
    """
    if date_obj is None:
        return "None"
    return date_obj.strftime("%Y-%m-%d") 