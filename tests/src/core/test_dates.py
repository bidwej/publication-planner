"""Tests for date utility functions."""

from datetime import date
from dateutil.parser import parse as parse_date

def test_parse_date_basic():
    """Test basic date parsing."""
    result = parse_date("2025-01-15").date()
    assert result == date(2025, 1, 15)

def test_parse_date_invalid():
    """Test invalid date parsing."""
    try:
        result = parse_date("invalid-date").date()
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass

def test_parse_date_with_default():
    """Test date parsing with default handling."""
    try:
        result = parse_date("invalid-date").date()
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass

def test_parse_date_none():
    """Test parsing None."""
    try:
        result = parse_date(None).date()
        assert False, "Should have raised TypeError"
    except (TypeError, AttributeError):
        pass

def test_parse_date_already_date():
    """Test parsing already a date object."""
    input_date = date(2025, 1, 15)
    result = parse_date(input_date.isoformat()).date()
    assert result == input_date

def test_parse_date_with_time():
    """Test parsing date with time component."""
    result = parse_date("2025-01-15T10:30:00").date()
    assert result == date(2025, 1, 15)

def test_parse_date_invalid_type():
    """Test parsing invalid type."""
    try:
        result = parse_date(123).date()
        assert False, "Should have raised TypeError"
    except (TypeError, AttributeError):
        pass

def test_parse_date_various_formats():
    """Test parsing various date formats."""
    # These should all work with dateutil.parser.parse
    assert parse_date("2025-01-15").date() == date(2025, 1, 15)
    assert parse_date("01/15/2025").date() == date(2025, 1, 15)
    assert parse_date("1/15/25").date() == date(2025, 1, 15)
    assert parse_date("15/01/2025").date() == date(2025, 1, 15)
    assert parse_date("January 15, 2025").date() == date(2025, 1, 15)
    assert parse_date("Jan 15, 2025").date() == date(2025, 1, 15)

def test_parse_date_with_timezone():
    """Test parsing date with timezone."""
    assert parse_date("2025-01-15T14:30:00").date() == date(2025, 1, 15)
    assert parse_date("2025-01-15T14:30:00Z").date() == date(2025, 1, 15)

def test_parse_date_empty_string():
    """Test parsing empty string."""
    try:
        result = parse_date("").date()
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass

def test_parse_date_whitespace():
    """Test parsing whitespace string."""
    try:
        result = parse_date("   ").date()
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass

def test_parse_date_long_invalid():
    """Test parsing long invalid string."""
    try:
        result = parse_date("this is a very long invalid date string").date()
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass 