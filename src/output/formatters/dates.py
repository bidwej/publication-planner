"""Date formatting utilities for output."""

from __future__ import annotations
from typing import Optional
from datetime import date, datetime

def format_date_display(input_date: date) -> str:
    """Format date for display (e.g., 'January 15, 2025')."""
    return input_date.strftime("%B %d, %Y")

def format_date_compact(input_date: date) -> str:
    """Format date compactly (e.g., '2025-01-15')."""
    return input_date.strftime("%Y-%m-%d")

def format_month_year(input_date: date) -> str:
    """Format date as month year (e.g., 'January 2025')."""
    return input_date.strftime("%B %Y")

def format_relative_time(input_date: date, reference_date: Optional[date] = None) -> str:
    """Format date as relative time from reference date."""
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
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        remaining_days = days % 7
        if remaining_days == 0:
            return f"{weeks} week{'s' if weeks != 1 else ''}"
        else:
            return f"{weeks} week{'s' if weeks != 1 else ''} {remaining_days} day{'s' if remaining_days != 1 else ''}"
    else:
        months = days // 30
        remaining_days = days % 30
        if remaining_days == 0:
            return f"{months} month{'s' if months != 1 else ''}"
        else:
            return f"{months} month{'s' if months != 1 else ''} {remaining_days} day{'s' if remaining_days != 1 else ''}" 