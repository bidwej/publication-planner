"""Date utilities for the paper planning system."""

from typing import Optional
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



