"""Tests for core date utility functions."""

from datetime import date
from core.dates import (
    parse_date_safe,
    add_working_days,
    is_working_day,
    days_between,
    months_between,
    format_date_for_display
)


class TestParseDateSafe:
    """Test the parse_date_safe function."""
    
    def test_valid_date_string(self):
        """Test parsing a valid date string."""
        result = parse_date_safe("2025-01-15")
        assert result == date(2025, 1, 15)
    
    def test_invalid_date_string(self):
        """Test parsing an invalid date string."""
        result = parse_date_safe("invalid-date")
        assert result is None
    
    def test_invalid_date_string_with_default(self):
        """Test parsing an invalid date string with default."""
        result = parse_date_safe("invalid-date", default=date(2025, 1, 1))
        assert result == date(2025, 1, 1)
    
    def test_none_input(self):
        """Test parsing None input."""
        result = parse_date_safe(None)
        assert result is None
    
    def test_date_object_input(self):
        """Test parsing a date object."""
        input_date = date(2025, 1, 15)
        result = parse_date_safe(input_date)
        assert result == input_date
    
    def test_datetime_string_with_time(self):
        """Test parsing datetime string with time component."""
        result = parse_date_safe("2025-01-15T10:30:00")
        assert result == date(2025, 1, 15)
    
    def test_non_string_input(self):
        """Test parsing non-string input."""
        result = parse_date_safe(123)
        assert result is None


class TestIsWorkingDay:
    """Test the is_working_day function."""
    
    def test_weekday(self):
        """Test a regular weekday."""
        # Monday
        test_date = date(2025, 1, 6)
        assert is_working_day(test_date) is True
    
    def test_weekend(self):
        """Test a weekend day."""
        # Saturday
        test_date = date(2025, 1, 4)
        assert is_working_day(test_date) is False
    
    def test_blackout_date(self):
        """Test a blackout date."""
        test_date = date(2025, 1, 6)
        blackout_dates = [date(2025, 1, 6)]
        assert is_working_day(test_date, blackout_dates) is False
    
    def test_weekend_with_blackout_dates(self):
        """Test weekend with blackout dates."""
        test_date = date(2025, 1, 4)  # Saturday
        blackout_dates = [date(2025, 1, 6)]  # Monday
        assert is_working_day(test_date, blackout_dates) is False
    
    def test_weekday_with_blackout_dates(self):
        """Test weekday with blackout dates."""
        test_date = date(2025, 1, 7)  # Tuesday
        blackout_dates = [date(2025, 1, 6)]  # Monday
        assert is_working_day(test_date, blackout_dates) is True


class TestAddWorkingDays:
    """Test the add_working_days function."""
    
    def test_add_zero_days(self):
        """Test adding zero working days."""
        start_date = date(2025, 1, 6)  # Monday
        result = add_working_days(start_date, 0)
        assert result == start_date
    
    def test_add_one_working_day(self):
        """Test adding one working day."""
        start_date = date(2025, 1, 6)  # Monday
        result = add_working_days(start_date, 1)
        assert result == date(2025, 1, 7)  # Tuesday
    
    def test_add_days_across_weekend(self):
        """Test adding days across a weekend."""
        start_date = date(2025, 1, 3)  # Friday
        result = add_working_days(start_date, 2)
        assert result == date(2025, 1, 7)  # Tuesday
    
    def test_add_days_with_blackout_dates(self):
        """Test adding days with blackout dates."""
        start_date = date(2025, 1, 6)  # Monday
        blackout_dates = [date(2025, 1, 7)]  # Tuesday
        result = add_working_days(start_date, 2, blackout_dates)
        assert result == date(2025, 1, 9)  # Thursday (Tuesday is blacked out)


class TestDaysBetween:
    """Test the days_between function."""
    
    def test_same_date(self):
        """Test calculating days between same date."""
        test_date = date(2025, 1, 15)
        result = days_between(test_date, test_date)
        assert result == 0
    
    def test_consecutive_days(self):
        """Test calculating days between consecutive days."""
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 16)
        result = days_between(start_date, end_date)
        assert result == 1
    
    def test_reverse_order(self):
        """Test calculating days in reverse order."""
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 10)
        result = days_between(start_date, end_date)
        assert result == -5


class TestMonthsBetween:
    """Test the months_between function."""
    
    def test_same_month(self):
        """Test calculating months between same month."""
        start_date = date(2025, 1, 15)
        end_date = date(2025, 1, 30)
        result = months_between(start_date, end_date)
        assert result == 0
    
    def test_consecutive_months(self):
        """Test calculating months between consecutive months."""
        start_date = date(2025, 1, 15)
        end_date = date(2025, 2, 15)
        result = months_between(start_date, end_date)
        assert result == 1
    
    def test_across_years(self):
        """Test calculating months across years."""
        start_date = date(2025, 12, 15)
        end_date = date(2026, 1, 15)
        result = months_between(start_date, end_date)
        assert result == 1
    
    def test_multiple_years(self):
        """Test calculating months across multiple years."""
        start_date = date(2025, 1, 15)
        end_date = date(2027, 3, 15)
        result = months_between(start_date, end_date)
        assert result == 26


class TestFormatDateForDisplay:
    """Test the format_date_for_display function."""
    
    def test_valid_date(self):
        """Test formatting a valid date."""
        test_date = date(2025, 1, 15)
        result = format_date_for_display(test_date)
        assert result == "2025-01-15"
    
    def test_none_date(self):
        """Test formatting None date."""
        result = format_date_for_display(None)
        assert result == "None"
    
    def test_single_digit_month_day(self):
        """Test formatting date with single digit month/day."""
        test_date = date(2025, 1, 5)
        result = format_date_for_display(test_date)
        assert result == "2025-01-05" 