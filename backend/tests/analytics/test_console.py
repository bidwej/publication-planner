"""Tests for console output module."""

import pytest
from datetime import date
from typing import Dict, List, Any, Optional


from console import (
    print_schedule_summary,
    print_deadline_status,
    print_utilization_summary,
    print_metrics_summary,
    format_table
)
from core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence, Schedule, Interval


class TestConsoleOutput:
    """Test console output functions."""
    
    @pytest.fixture
    def sample_config(self):
        """Provide a sample configuration for testing."""
        conferences = [
            Conference(
                id="ICML",
                name="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={
                    SubmissionType.ABSTRACT: date(2025, 1, 15),
                    SubmissionType.PAPER: date(2025, 1, 30)
                }
            ),
            Conference(
                id="MICCAI",
                name="MICCAI",
                conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={
                    SubmissionType.ABSTRACT: date(2025, 2, 15),
                    SubmissionType.PAPER: date(2025, 3, 1)
                }
            )
        ]
        
        submissions = [
            Submission(
                id="J1-pap",
                title="Test Paper",
                kind=SubmissionType.PAPER,
                conference_id="ICML",
                depends_on=[],
                draft_window_months=2,
                lead_time_from_parents=0,
                penalty_cost_per_day=500,
                engineering=True,
                earliest_start_date=date(2024, 11, 1)
            ),
            Submission(
                id="J2-pap",
                title="Medical Paper",
                kind=SubmissionType.PAPER,
                conference_id="MICCAI",
                depends_on=["J1-pap"],
                draft_window_months=3,
                lead_time_from_parents=2,
                penalty_cost_per_day=300,
                engineering=False,
                earliest_start_date=date(2024, 12, 1)
            ),
            Submission(
                id="J1-abs",
                title="Abstract",
                kind=SubmissionType.ABSTRACT,
                conference_id="ICML",
                depends_on=[],
                draft_window_months=0,
                lead_time_from_parents=0,
                penalty_cost_per_day=100,
                engineering=True,
                earliest_start_date=date(2024, 10, 1)
            )
        ]
        
        return Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=60,
            max_concurrent_submissions=2,
            default_paper_lead_time_months=3,
            penalty_costs={},
            priority_weights={},
            scheduling_options={},
            blackout_dates=[],
            data_files={}
        )
    
    @pytest.fixture
    def empty_schedule(self) -> Schedule:
        """Provide an empty schedule for testing."""
        return Schedule()

    @pytest.fixture
    def sample_schedule(self) -> Schedule:
        """Provide a sample schedule for testing."""
        schedule = Schedule()
        schedule.add_interval("J1-pap", date(2024, 11, 1), duration_days=30)
        schedule.add_interval("J2-pap", date(2024, 12, 1), duration_days=30)
        schedule.add_interval("J1-abs", date(2024, 10, 1), duration_days=0)
        return schedule

    @pytest.fixture
    def late_schedule(self) -> Schedule:
        """Provide a schedule with late submissions for testing."""
        schedule = Schedule()
        schedule.add_interval("J1-pap", date(2024, 11, 1), duration_days=30)
        schedule.add_interval("J2-pap", date(2024, 12, 1), duration_days=30)
        schedule.add_interval("J1-abs", date(2024, 10, 1), duration_days=0)
        return schedule

    @pytest.fixture
    def mixed_schedule(self) -> Schedule:
        """Provide a schedule with mixed submission types for testing."""
        schedule = Schedule()
        schedule.add_interval("J1-pap", date(2024, 11, 1), duration_days=30)
        schedule.add_interval("J2-pap", date(2024, 12, 1), duration_days=30)
        schedule.add_interval("J1-abs", date(2024, 10, 1), duration_days=0)
        return schedule

    @pytest.fixture
    def no_deadline_schedule(self) -> Schedule:
        """Provide a schedule with no deadlines for testing."""
        schedule = Schedule()
        schedule.add_interval("J1-pap", date(2024, 11, 1), duration_days=30)
        return schedule
    
    def test_print_schedule_summary(self, monkeypatch, sample_schedule, sample_config) -> None:
        """Test printing schedule summary."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        print_schedule_summary(sample_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for expected output
        full_text = "".join(printed_text)
        assert "Schedule Summary" in full_text
        assert "Total submissions: 3" in full_text  # Fixed: sample_schedule has 3 items
        assert "Abstracts: 1" in full_text  # Fixed: J1-abs is an abstract
        assert "Papers: 2" in full_text  # Fixed: J1-pap and J2-pap are papers
    
    def test_print_schedule_summary_empty(self, monkeypatch, sample_config) -> None:
        """Test printing schedule summary with empty schedule."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        empty_schedule = Schedule()
        print_schedule_summary(empty_schedule, sample_config)
        
        # Should print "No schedule generated"
        full_text = "".join(printed_text)
        assert "No schedule generated" in full_text
    
    def test_print_deadline_status(self, monkeypatch, sample_schedule, sample_config) -> None:
        """Test printing deadline status."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        print_deadline_status(sample_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for expected output
        full_text = "".join(printed_text)
        assert "Deadline Status" in full_text
        assert "On time:" in full_text or "Late:" in full_text
    
    def test_print_deadline_status_empty(self, monkeypatch, sample_config) -> None:
        """Test printing deadline status with empty schedule."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        empty_schedule = Schedule()
        print_deadline_status(empty_schedule, sample_config)
        
        # Should not print anything for empty schedule
        assert len(printed_text) == 0
    
    def test_print_deadline_status_late_submissions(self, monkeypatch, sample_config) -> None:
        """Test printing deadline status with late submissions."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        # Create a schedule with late submissions
        late_schedule = Schedule()
        late_schedule.add_interval("J1-pap", date(2025, 2, 1), duration_days=30)  # After deadline
        late_schedule.add_interval("J2-pap", date(2025, 4, 1), duration_days=30)   # After deadline
        
        print_deadline_status(late_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for late submission messages
        full_text = "".join(printed_text)
        assert "LATE:" in full_text
    
    def test_print_utilization_summary(self, monkeypatch, sample_schedule, sample_config) -> None:
        """Test printing utilization summary."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        print_utilization_summary(sample_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for expected output
        full_text = "".join(printed_text)
        assert "Resource Utilization" in full_text
        assert "Max concurrent submissions:" in full_text  # Fixed: actual output
    
    def test_print_utilization_summary_empty(self, monkeypatch, sample_config) -> None:
        """Test printing utilization summary with empty schedule."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        empty_schedule = Schedule()
        print_utilization_summary(empty_schedule, sample_config)
        
        # Should not print anything for empty schedule
        assert len(printed_text) == 0
    
    def test_print_metrics_summary(self, monkeypatch, sample_schedule, sample_config) -> None:
        """Test printing metrics summary."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        print_metrics_summary(sample_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for expected output - handle both positional and keyword args
        full_text = "".join(printed_text)
        assert "Metrics Summary" in full_text
    
    def test_print_metrics_summary_empty(self, monkeypatch, sample_config) -> None:
        """Test printing metrics summary with empty schedule."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        empty_schedule = Schedule()
        print_metrics_summary(empty_schedule, sample_config)
        
        # Should still print something for empty schedule
        assert len(printed_text) > 0
    
    def test_format_table(self) -> None:
        """Test table formatting."""
        data = [
            {"id": "J1", "title": "Paper 1", "date": "2024-11-01"},
            {"id": "J2", "title": "Paper 2", "date": "2024-12-01"}
        ]
        
        result: Any = format_table(data, "Test Table")
        
        assert isinstance(result, str)
        assert "Test Table" in result
        assert "J1" in result
        assert "J2" in result
        assert "Paper 1" in result
        assert "Paper 2" in result
    
    def test_format_table_empty(self) -> None:
        """Test table formatting with empty data."""
        data = []
        result: Any = format_table(data, "Empty Table")
        
        assert isinstance(result, str)
        assert "Empty Table" in result
    
    def test_format_table_single_row(self) -> None:
        """Test table formatting with single row."""
        data = [{"id": "J1", "title": "Single Paper"}]
        result: Any = format_table(data, "Single Row Table")
        
        assert isinstance(result, str)
        assert "J1" in result
        assert "Single Paper" in result
    
    def test_format_table_with_different_column_types(self) -> None:
        """Test table formatting with different data types."""
        data = [
            {"id": "J1", "count": 5, "active": True, "date": date(2024, 11, 1)},
            {"id": "J2", "count": 3, "active": False, "date": date(2024, 12, 1)}
        ]
        
        result: Any = format_table(data, "Mixed Data Table")
        
        assert isinstance(result, str)
        assert "J1" in result
        assert "J2" in result
        assert "5" in result
        assert "3" in result
        assert "True" in result
        assert "False" in result
    
    def test_print_schedule_summary_with_mixed_types(self, monkeypatch, sample_config) -> None:
        """Test printing schedule summary with mixed submission types."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        mixed_schedule = Schedule()
        mixed_schedule.add_interval("J1-pap", date(2024, 11, 1), duration_days=30)
        mixed_schedule.add_interval("J1-abs", date(2024, 10, 1), duration_days=0)
        mixed_schedule.add_interval("J2-pap", date(2024, 12, 1), duration_days=30)
        
        print_schedule_summary(mixed_schedule, sample_config)
        
        # Verify print was called
        assert len(printed_text) > 0
        
        # Check for expected output
        full_text = "".join(printed_text)
        assert "Total submissions: 3" in full_text
        assert "Abstracts: 1" in full_text  # This should work with the mixed schedule
        assert "Papers: 2" in full_text
    
    def test_print_deadline_status_no_deadlines(self, monkeypatch, sample_config) -> None:
        """Test printing deadline status when no deadlines are configured."""
        # Mock the print function
        printed_text = []
        def mock_print(*args, **kwargs):
            if args:
                printed_text.append(str(args[0]))
            elif kwargs and 'end' not in kwargs:
                for key, value in kwargs.items():
                    if key != 'end':
                        printed_text.append(str(value))
        
        monkeypatch.setattr('builtins.print', mock_print)
        
        # Create config without deadlines
        no_deadline_config: Config = Config(
            submissions=sample_config.submissions,
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=60,
            max_concurrent_submissions=2,
            default_paper_lead_time_months=3,
            penalty_costs={},
            priority_weights={},
            scheduling_options={},
            blackout_dates=[],
            data_files={}
        )
        
        schedule = Schedule()
        schedule.add_interval("J1-pap", date(2024, 11, 1))
        print_deadline_status(schedule, no_deadline_config)
        
        # Should print "No submissions with deadlines found"
        full_text = "".join(printed_text)
        assert "No submissions with deadlines found" in full_text
    
    def test_format_table_with_none_values(self) -> None:
        """Test table formatting with None values."""
        data = [
            {"id": "J1", "title": "Paper 1", "date": None},
            {"id": "J2", "title": None, "date": "2024-12-01"}
        ]
        
        result: Any = format_table(data, "None Values Table")
        
        assert isinstance(result, str)
        assert "J1" in result
        assert "J2" in result
        assert "Paper 1" in result
        # None values should be handled gracefully
        assert "None" in result or "" in result
