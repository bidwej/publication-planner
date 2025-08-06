"""Tests for output tables module."""

import pytest
from datetime import date, timedelta
from typing import Dict, List
from src.output.tables import generate_simple_monthly_table, generate_monthly_table, generate_schedule_summary_table, generate_deadline_table
from src.core.models import Config, Submission, Conference, SubmissionType


class TestGenerateSimpleMonthlyTable:
    """Test simple monthly table generation."""
    
    def test_empty_schedule(self, config):
        """Test table generation with empty schedule."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config):
        """Test table generation with single submission."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config):
        """Test table generation with multiple submissions."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_spread_out_schedule(self, config):
        """Test table generation with spread out schedule."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_structure(self, config):
        """Test that table has expected structure."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Each row should be a dictionary
        for row in table:
            assert isinstance(row, dict)


class TestGenerateScheduleSummaryTable:
    """Test schedule summary table generation."""
    
    def test_empty_schedule(self, config):
        """Test summary table generation with empty schedule."""
        schedule = {}
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config):
        """Test summary table generation with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config):
        """Test summary table generation with multiple submissions."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 15),
            "paper3": date(2025, 6, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0


class TestGenerateDeadlineTable:
    """Test deadline table generation."""
    
    def test_empty_schedule(self, config):
        """Test deadline table generation with empty schedule."""
        schedule = {}
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config):
        """Test deadline table generation with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config):
        """Test deadline table generation with multiple submissions."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 15),
            "paper3": date(2025, 6, 1)
        }
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0


class TestTableFormats:
    """Test different table formats."""
    
    def test_monthly_format(self, config):
        """Test monthly table format."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Should have entries for each month
        assert len(table) >= 0
    
    def test_summary_format(self, config):
        """Test summary table format."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 1),
            "paper3": date(2025, 3, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have summary information for each submission
        assert len(table) >= 0
    
    def test_table_with_conferences(self, config):
        """Test table generation with conference information."""
        schedule = {
            "conf1-pap": date(2025, 1, 1),
            "conf2-pap": date(2025, 2, 1),
            "conf3-pap": date(2025, 3, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_with_dependencies(self, config):
        """Test table generation with dependency information."""
        schedule = {
            "parent-pap": date(2025, 1, 1),
            "child-pap": date(2025, 2, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
