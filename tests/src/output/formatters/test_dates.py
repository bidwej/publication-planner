"""Tests for the formatters dates module."""

from datetime import date, datetime, timedelta

from output.formatters.dates import (
    format_date_display, format_relative_time, format_duration_days,
    format_month_year
)


class TestFormatDateDisplay:
    """Test the format_date_display function."""

    def test_format_date_display_basic(self):
        """Test basic date formatting."""
        test_date = date(2024, 5, 15)
        result = format_date_display(test_date)
        assert result == "2024-05-15"

    def test_format_date_display_none(self):
        """Test date formatting with None."""
        result = format_date_display(None)
        assert result == "N/A"

    def test_format_date_display_custom_format(self):
        """Test date formatting with custom format."""
        test_date = date(2024, 5, 15)
        result = format_date_display(test_date, format_str="%B %d, %Y")
        assert result == "May 15, 2024"

    def test_format_date_display_datetime(self):
        """Test date formatting with datetime object."""
        test_datetime = datetime(2024, 5, 15, 10, 30, 0)
        result = format_date_display(test_datetime)
        assert result == "2024-05-15"


class TestFormatRelativeTime:
    """Test the format_relative_time function."""

    def test_format_relative_time_future(self):
        """Test relative time formatting for future date."""
        future_date = date.today() + timedelta(days=30)
        result = format_relative_time(future_date)
        assert "30 days" in result or "1 month" in result

    def test_format_relative_time_past(self):
        """Test relative time formatting for past date."""
        past_date = date.today() - timedelta(days=30)
        result = format_relative_time(past_date)
        assert "30 days ago" in result or "1 month ago" in result

    def test_format_relative_time_today(self):
        """Test relative time formatting for today."""
        today = date.today()
        result = format_relative_time(today)
        assert result == "Today"

    def test_format_relative_time_yesterday(self):
        """Test relative time formatting for yesterday."""
        yesterday = date.today() - timedelta(days=1)
        result = format_relative_time(yesterday)
        assert result == "Yesterday"

    def test_format_relative_time_tomorrow(self):
        """Test relative time formatting for tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        result = format_relative_time(tomorrow)
        assert result == "Tomorrow"

    def test_format_relative_time_none(self):
        """Test relative time formatting with None."""
        result = format_relative_time(None)
        assert result == "Unknown"


class TestFormatDurationDays:
    """Test the format_duration_days function."""

    def test_format_duration_days_zero(self):
        """Test duration formatting for zero days."""
        result = format_duration_days(0)
        assert result == "0 days"

    def test_format_duration_days_one(self):
        """Test duration formatting for one day."""
        result = format_duration_days(1)
        assert result == "1 day"

    def test_format_duration_days_multiple(self):
        """Test duration formatting for multiple days."""
        result = format_duration_days(30)
        assert result == "30 days"

    def test_format_duration_days_negative(self):
        """Test duration formatting for negative days."""
        result = format_duration_days(-5)
        assert result == "-5 days"

    def test_format_duration_days_large(self):
        """Test duration formatting for large number of days."""
        result = format_duration_days(365)
        assert result == "365 days"





class TestFormatMonthYear:
    """Test the format_month_year function."""

    def test_format_month_year_basic(self):
        """Test basic month-year formatting."""
        test_date = date(2024, 5, 15)
        result = format_month_year(test_date)
        assert result == "May 2024"

    def test_format_month_year_january(self):
        """Test month-year formatting for January."""
        test_date = date(2024, 1, 1)
        result = format_month_year(test_date)
        assert result == "January 2024"

    def test_format_month_year_december(self):
        """Test month-year formatting for December."""
        test_date = date(2024, 12, 31)
        result = format_month_year(test_date)
        assert result == "December 2024"

    def test_format_month_year_none(self):
        """Test month-year formatting with None."""
        result = format_month_year(None)
        assert result == "N/A"

    def test_format_month_year_custom_format(self):
        """Test month-year formatting with custom format."""
        test_date = date(2024, 5, 15)
        result = format_month_year(test_date, format_str="%m/%Y")
        assert result == "05/2024"
