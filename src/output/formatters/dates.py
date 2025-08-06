"""Date formatting utilities for output."""

from __future__ import annotations
from typing import Optional, Union
from datetime import date, datetime

def format_date_display(input_date: Optional[Union[date, datetime]], format_str: str = "%Y-%m-%d") -> str:
    """Format date for display (e.g., '2025-01-15')."""
    if input_date is None:
        return "N/A"
    if isinstance(input_date, datetime):
        input_date = input_date.date()
    return input_date.strftime(format_str)

def format_date_compact(input_date: date) -> str:
    """Format date compactly (e.g., '2025-01-15')."""
    return input_date.strftime("%Y-%m-%d")

def format_month_year(input_date: Optional[date], format_str: str = "%B %Y") -> str:
    """Format date as month year (e.g., 'January 2025')."""
    if input_date is None:
        return "N/A"
    return input_date.strftime(format_str)

def format_relative_time(input_date: Optional[date], reference_date: Optional[date] = None) -> str:
    """Format date as relative time from reference date."""
    if input_date is None:
        return "Unknown"
    
    if reference_date is None:
        reference_date = datetime.now().date()
    
    delta = input_date - reference_date
    days = delta.days
    
    if days == 0:
        return "Today"
    elif days == 1:
        return "Tomorrow"
    elif days == -1:
        return "Yesterday"
    elif days > 0:
        if days < 7:
            return f"In {days} days"
        elif days < 30:
            weeks = days // 7
            return f"In {weeks} week{'s' if weeks != 1 else ''}"
        else:
            months = (input_date.year - reference_date.year) * 12 + input_date.month - reference_date.month
            return f"In {months} month{'s' if months != 1 else ''}"
    else:
        if days > -7:
            return f"{abs(days)} days ago"
        elif days > -30:
            weeks = abs(days) // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = (reference_date.year - input_date.year) * 12 + reference_date.month - input_date.month
            return f"{months} month{'s' if months != 1 else ''} ago"

def format_duration_days(days: int) -> str:
    """Format duration in days as human-readable string."""
    if days == 0:
        return "0 days"
    elif days == 1:
        return "1 day"
    elif days == -1:
        return "-1 day"
    else:
        return f"{days} days" 