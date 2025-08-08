"""Tests for the formatters dates module."""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

from src.analytics.formatters.dates import (
    format_date_display, format_relative_time, format_duration_days,
    format_month_year
)


class TestFormatDateDisplay:
    """Test the format_date_display function."""

    def test_format_date_display_basic(self) -> None:
        """Test basic date formatting."""
        test_date: date = date(2024, 5, 15)
        result: Any = format_date_display(test_date)
        assert result == "2024-05-15"

    def test_format_date_display_none(self) -> None:
        """Test date formatting with None."""
        result: Any = format_date_display(None)
        assert result == "N/A"

    def test_format_date_display_custom_format(self) -> None:
        """Test date formatting with custom format."""
        test_date: date = date(2024, 5, 15)
        result: Any = format_date_display(test_date, format_str="%B %d, %Y")
        assert result == "May 15, 2024"

    def test_format_date_display_datetime(self) -> None:
        """Test date formatting with datetime object."""
        test_datetime: datetime = datetime(2024, 5, 15, 10, 30, 0)
        result: Any = format_date_display(test_datetime)
        assert result == "2024-05-15"


class TestFormatRelativeTime:
    """Test the format_relative_time function."""

    def test_format_relative_time_future(self) -> None:
        """Test relative time formatting for future date."""
        future_date: date = date.today() + timedelta(days=30)
        result: Any = format_relative_time(future_date)
        assert "30 days" in result or "1 month" in result

    def test_format_relative_time_past(self) -> None:
        """Test relative time formatting for past date."""
        past_date: date = date.today() - timedelta(days=30)
        result: Any = format_relative_time(past_date)
        assert "30 days ago" in result or "1 month ago" in result

    def test_format_relative_time_today(self) -> None:
        """Test relative time formatting for today."""
        today: date = date.today()
        result: Any = format_relative_time(today)
        assert result == "Today"

    def test_format_relative_time_yesterday(self) -> None:
        """Test relative time formatting for yesterday."""
        yesterday: date = date.today() - timedelta(days=1)
        result: Any = format_relative_time(yesterday)
        assert result == "Yesterday"

    def test_format_relative_time_tomorrow(self) -> None:
        """Test relative time formatting for tomorrow."""
        tomorrow: date = date.today() + timedelta(days=1)
        result: Any = format_relative_time(tomorrow)
        assert result == "Tomorrow"

    def test_format_relative_time_none(self) -> None:
        """Test relative time formatting with None."""
        result: Any = format_relative_time(None)
        assert result == "Unknown"


class TestFormatDurationDays:
    """Test the format_duration_days function."""

    def test_format_duration_days_zero(self) -> None:
        """Test duration formatting for zero days."""
        result: Any = format_duration_days(0)
        assert result == "0 days"

    def test_format_duration_days_one(self) -> None:
        """Test duration formatting for one day."""
        result: Any = format_duration_days(1)
        assert result == "1 day"

    def test_format_duration_days_multiple(self) -> None:
        """Test duration formatting for multiple days."""
        result: Any = format_duration_days(30)
        assert result == "30 days"

    def test_format_duration_days_negative(self) -> None:
        """Test duration formatting for negative days."""
        result: Any = format_duration_days(-5)
        assert result == "-5 days"

    def test_format_duration_days_large(self) -> None:
        """Test duration formatting for large number of days."""
        result: Any = format_duration_days(365)
        assert result == "365 days"


class TestFormatMonthYear:
    """Test the format_month_year function."""

    def test_format_month_year_basic(self) -> None:
        """Test basic month-year formatting."""
        test_date: date = date(2024, 5, 15)
        result: Any = format_month_year(test_date)
        assert result == "May 2024"

    def test_format_month_year_january(self) -> None:
        """Test month-year formatting for January."""
        test_date: date = date(2024, 1, 1)
        result: Any = format_month_year(test_date)
        assert result == "January 2024"

    def test_format_month_year_december(self) -> None:
        """Test month-year formatting for December."""
        test_date: date = date(2024, 12, 31)
        result: Any = format_month_year(test_date)
        assert result == "December 2024"

    def test_format_month_year_none(self) -> None:
        """Test month-year formatting with None."""
        result: Any = format_month_year(None)
        assert result == "N/A"

    def test_format_month_year_custom_format(self) -> None:
        """Test month-year formatting with custom format."""
        test_date: date = date(2024, 5, 15)
        result: Any = format_month_year(test_date, format_str="%m/%Y")
        assert result == "05/2024"
