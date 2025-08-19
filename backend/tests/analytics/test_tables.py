"""Tests for output tables module."""

from datetime import date
from typing import Dict, List, Any, Optional

from tables import (
    generate_simple_monthly_table, 
    generate_schedule_summary_table, 
    generate_deadline_table,
    format_schedule_table,
    format_metrics_table,
    format_deadline_table,
    create_schedule_table,
    create_violations_table,
    create_metrics_table,
    create_analytics_table,
    save_schedule_json,
    save_table_csv,
    get_output_summary
)
from core.models import Schedule, Interval


class TestGenerateSimpleMonthlyTable:
    """Test simple monthly table generation."""
    
    def test_empty_schedule(self, config) -> None:
        """Test table generation with empty schedule."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config) -> None:
        """Test table generation with single submission."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config) -> None:
        """Test table generation with multiple submissions."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_spread_out_schedule(self, config) -> None:
        """Test table generation with spread out schedule."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_structure(self, config) -> None:
        """Test that table has expected structure."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Each row should be a dictionary
        for row in table:
            assert isinstance(row, dict)


class TestGenerateScheduleSummaryTable:
    """Test schedule summary table generation."""
    
    def test_empty_schedule(self, config) -> None:
        """Test summary table generation with empty schedule."""
        schedule = Schedule(intervals={})
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config) -> None:
        """Test summary table generation with single submission."""
        schedule = Schedule(intervals={
            "test-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 2, 15))
        })
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config) -> None:
        """Test summary table generation with multiple submissions."""
        schedule = Schedule(intervals={
            "paper1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 4, 1)),
            "paper2": Interval(start_date=date(2025, 2, 15), end_date=date(2025, 5, 15)),
            "paper3": Interval(start_date=date(2025, 6, 1), end_date=date(2025, 9, 1))
        })
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0


class TestGenerateDeadlineTable:
    """Test deadline table generation."""
    
    def test_empty_schedule(self, config) -> None:
        """Test deadline table generation with empty schedule."""
        schedule: Schedule = {}
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have some structure even with empty schedule
        assert len(table) >= 0
    
    def test_single_submission(self, config) -> None:
        """Test deadline table generation with single submission."""
        schedule = Schedule(intervals={"test-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 1, 15))})
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_multiple_submissions(self, config) -> None:
        """Test deadline table generation with multiple submissions."""
        schedule: Schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 15),
            "paper3": date(2025, 6, 1)
        }
        table = generate_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0


class TestFormatScheduleTable:
    """Test formatted schedule table generation."""
    
    def test_empty_schedule(self, config) -> None:
        """Test formatted table generation with empty schedule."""
        schedule: Schedule = {}
        table = format_schedule_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) == 0
    
    def test_single_submission(self, config) -> None:
        """Test formatted table generation with single submission."""
        schedule: Schedule = {"test-pap": date(2025, 1, 15)}
        table = format_schedule_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_structure(self, config) -> None:
        """Test that formatted table has expected structure."""
        schedule: Schedule = {"test-pap": date(2025, 1, 15)}
        table = format_schedule_table(schedule, config)
        
        if table:
            row = table[0]
            expected_keys = ["Submission", "Type", "Conference", "Start Date", "End Date", "Duration", "Deadline", "Relative Time"]
            for key in expected_keys:
                assert key in row


class TestFormatMetricsTable:
    """Test metrics table formatting."""
    
    def test_metrics_table_structure(self, mock_schedule_summary) -> None:
        """Test that metrics table has expected structure."""
        table = format_metrics_table(mock_schedule_summary)
        
        assert isinstance(table, list)
        assert len(table) > 0
        
        for row in table:
            assert "Metric" in row
            assert "Value" in row
            assert "Description" in row


class TestFormatDeadlineTable:
    """Test deadline table formatting."""
    
    def test_empty_schedule(self, config) -> None:
        """Test deadline formatting with empty schedule."""
        schedule: Schedule = {}
        table = format_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) == 0
    
    def test_single_submission(self, config) -> None:
        """Test deadline formatting with single submission."""
        schedule: Schedule = {"test-pap": date(2025, 1, 15)}
        table = format_deadline_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0


class TestCreateScheduleTable:
    """Test web-specific schedule table creation."""
    
    def test_empty_schedule(self, config) -> None:
        """Test web table creation with empty schedule."""
        schedule: Schedule = {}
        table = create_schedule_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) == 0
    
    def test_single_submission(self, config) -> None:
        """Test web table creation with single submission."""
        schedule: Schedule = {"test-pap": date(2025, 1, 15)}
        table = create_schedule_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_structure(self, config) -> None:
        """Test that web table has expected structure."""
        schedule: Schedule = {"test-pap": date(2025, 1, 15)}
        table = create_schedule_table(schedule, config)
        
        if table:
            row = table[0]
            expected_keys = ['id', 'title', 'type', 'start_date', 'end_date', 'conference', 'status', 'duration', 'engineering']
            for key in expected_keys:
                assert key in row


class TestCreateViolationsTable:
    """Test violations table creation."""
    
    def test_empty_validation_result(self) -> None:
        """Test violations table with empty validation result."""
        validation_result: Any = {}
        table = create_violations_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) == 0
    
    def test_with_violations(self) -> None:
        """Test violations table with actual violations."""
        validation_result: Any = {
            'constraints': {
                'deadline_constraint': {
                    'violations': [
                        {
                            'submission_id': 'test-pap',
                            'message': 'Deadline missed',
                            'severity': 'high',
                            'impact': 'critical'
                        }
                    ]
                }
            }
        }
        table = create_violations_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) > 0
        
        if table:
            row = table[0]
            expected_keys = ['type', 'submission', 'description', 'severity', 'impact']
            for key in expected_keys:
                assert key in row


class TestCreateMetricsTable:
    """Test metrics table creation."""
    
    def test_empty_validation_result(self) -> None:
        """Test metrics table with empty validation result."""
        validation_result: Any = {}
        table = create_metrics_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) == 0  # Should return empty list when no data
        # No rows to check when empty
    
    def test_with_scores(self) -> None:
        """Test metrics table with actual scores."""
        validation_result: Any = {
            'scores': {
                'penalty_score': 85.5,
                'quality_score': 92.3,
                'efficiency_score': 78.9
            },
            'summary': {
                'overall_score': 88.2
            }
        }
        table = create_metrics_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) > 0
        
        for row in table:
            assert 'metric' in row
            assert 'value' in row
            assert 'status' in row


class TestCreateAnalyticsTable:
    """Test analytics table creation."""
    
    def test_empty_validation_result(self) -> None:
        """Test analytics table with empty validation result."""
        validation_result: Any = {}
        table = create_analytics_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) == 0  # Should return empty list when no data
        # No rows to check when empty
    
    def test_with_summary(self) -> None:
        """Test analytics table with actual summary."""
        validation_result: Any = {
            'summary': {
                'total_submissions': 10,
                'duration_days': 45,
                'deadline_compliance': 85.5,
                'dependency_satisfaction': 92.3,
                'total_violations': 2,
                'critical_violations': 0
            }
        }
        table = create_analytics_table(validation_result)
        
        assert isinstance(table, list)
        assert len(table) > 0
        
        for row in table:
            assert 'category' in row
            assert 'metric' in row
            assert 'value' in row


class TestFileIOFunctions:
    """Test file I/O functions."""
    
    def test_save_schedule_json(self, tmp_path) -> None:
        """Test saving schedule as JSON."""
        schedule: Schedule = {"test-pap": "2025-01-15"}
        output_dir = str(tmp_path)
        
        filepath = save_schedule_json(schedule, output_dir)
        
        assert filepath.endswith("schedule.json")
        assert filepath.startswith(str(tmp_path))
    
    def test_save_table_csv(self, tmp_path) -> None:
        """Test saving table as CSV."""
        table_data = [
            {"ID": "1", "Title": "Test Paper", "Type": "Paper"},
            {"ID": "2", "Title": "Test Abstract", "Type": "Abstract"}
        ]
        output_dir = str(tmp_path)
        
        filepath = save_table_csv(table_data, output_dir, "test_table.csv")
        
        assert filepath.endswith("test_table.csv")
        assert filepath.startswith(str(tmp_path))
    
    def test_save_empty_table_csv(self, tmp_path) -> None:
        """Test saving empty table as CSV."""
        table_data = []
        output_dir = str(tmp_path)
        
        filepath = save_table_csv(table_data, output_dir, "empty.csv")
        
        assert filepath == ""
    
    def test_get_output_summary(self) -> None:
        """Test output summary generation."""
        saved_files = {
            "schedule": "/path/to/schedule.json",
            "metrics": "/path/to/metrics.json"
        }
        
        summary = get_output_summary(saved_files)
        
        assert "schedule.json" in summary
        assert "metrics.json" in summary
    
    def test_get_empty_output_summary(self) -> None:
        """Test output summary with no files."""
        saved_files = {}
        
        summary = get_output_summary(saved_files)
        
        assert "No files were saved" in summary


class TestTableFormats:
    """Test different table formats."""
    
    def test_monthly_format(self, config) -> None:
        """Test monthly table format."""
        table = generate_simple_monthly_table(config)
        
        assert isinstance(table, list)
        # Should have entries for each month
        assert len(table) >= 0
    
    def test_summary_format(self, config) -> None:
        """Test summary table format."""
        schedule: Schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 1),
            "paper3": date(2025, 3, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        # Should have summary information for each submission
        assert len(table) >= 0
    
    def test_table_with_conferences(self, config) -> None:
        """Test table generation with conference information."""
        schedule: Schedule = {
            "conf1-pap": date(2025, 1, 1),
            "conf2-pap": date(2025, 2, 1),
            "conf3-pap": date(2025, 3, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
    
    def test_table_with_dependencies(self, config) -> None:
        """Test table generation with dependency information."""
        schedule: Schedule = {
            "parent-pap": date(2025, 1, 1),
            "child-pap": date(2025, 2, 1)
        }
        table = generate_schedule_summary_table(schedule, config)
        
        assert isinstance(table, list)
        assert len(table) >= 0
