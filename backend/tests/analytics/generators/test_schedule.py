"""Tests for output generators schedule module."""

from datetime import date
from pathlib import Path
from typing import Dict, List, Any

import pytest

from src.generators.schedule import (
    create_output_directory,
    save_all_outputs,
    generate_schedule_summary,
    generate_schedule_metrics
)
from core.models import Config, ScheduleSummary, ScheduleMetrics


class TestCreateOutputDirectory:
    """Test the create_output_directory function."""

    def test_create_output_directory_basic(self, tmp_path: Path) -> None:
        """Test basic directory creation."""
        base_dir: str = str(tmp_path)
        output_dir: str = create_output_directory(base_dir)
        
        assert output_dir.startswith(base_dir)
        assert "output_" in output_dir
        assert Path(output_dir).exists()
        assert Path(output_dir).is_dir()

    def test_create_output_directory_default(self, tmp_path: Path, monkeypatch) -> None:
        """Test directory creation with default base_dir."""
        # Create simple mock objects
        mock_path_instance = type('MockPath', (), {
            '__truediv__': lambda self, other: self,
            'mkdir': lambda self, **kwargs: None
        })()
        
        def mock_path(*args, **kwargs):
            return mock_path_instance
        
        monkeypatch.setattr('src.generators.schedule.Path', mock_path)
        
        output_dir: str = create_output_directory()
        assert output_dir is not None


class TestSaveAllOutputs:
    """Test the save_all_outputs function."""

    def test_save_all_outputs_basic(self, tmp_path: Path, monkeypatch) -> None:
        """Test save all outputs with basic data."""
        schedule: Dict[str, date] = {"paper1": date(2024, 1, 1)}
        schedule_table: List[Dict[str, str]] = [{"id": "paper1", "date": "2024-01-01"}]
        metrics_table: List[Dict[str, str]] = [{"metric": "score", "value": "0.85"}]
        deadline_table: List[Dict[str, str]] = [{"deadline": "2024-02-01", "status": "met"}]
        
        # Create a simple mock metrics object
        metrics = type('MockScheduleSummary', (), {
            'total_submissions': 1,
            'completion_rate': 100.0,
            'quality_score': 0.85
        })()
        
        output_dir: str = str(tmp_path)
        
        # Mock the save functions
        def mock_save_schedule(*args, **kwargs):
            return "/test/schedule.json"
        
        def mock_save_csv(*args, **kwargs):
            return "/test/table.csv"
        
        def mock_save_metrics(*args, **kwargs):
            return "/test/metrics.json"
        
        monkeypatch.setattr('src.generators.schedule.save_schedule_json', mock_save_schedule)
        monkeypatch.setattr('src.generators.schedule.save_table_csv', mock_save_csv)
        monkeypatch.setattr('src.generators.schedule.save_metrics_json', mock_save_metrics)
        
        result: Dict[str, str] = save_all_outputs(schedule, schedule_table, metrics_table, deadline_table, metrics, output_dir)  # type: ignore
        
        assert isinstance(result, dict)
        assert "schedule" in result
        assert "schedule_table" in result
        assert "metrics_table" in result
        assert "deadline_table" in result
        assert "metrics" in result

    def test_save_all_outputs_empty_tables(self, tmp_path: Path, monkeypatch) -> None:
        """Test save all outputs with empty tables."""
        schedule: Dict[str, date] = {"paper1": date(2024, 1, 1)}
        schedule_table: List[Dict[str, str]] = []
        metrics_table: List[Dict[str, str]] = []
        deadline_table: List[Dict[str, str]] = []
        
        # Create a simple mock metrics object
        metrics = type('MockScheduleSummary', (), {
            'total_submissions': 1,
            'completion_rate': 100.0,
            'quality_score': 0.85
        })()
        
        output_dir: str = str(tmp_path)
        
        # Mock the save functions
        def mock_save_schedule(*args, **kwargs):
            return "/test/schedule.json"
        
        def mock_save_metrics(*args, **kwargs):
            return "/test/metrics.json"
        
        monkeypatch.setattr('src.generators.schedule.save_schedule_json', mock_save_schedule)
        monkeypatch.setattr('src.generators.schedule.save_metrics_json', mock_save_metrics)
        
        result: Dict[str, str] = save_all_outputs(schedule, schedule_table, metrics_table, deadline_table, metrics, output_dir)  # type: ignore
        
        assert isinstance(result, dict)


class TestGenerateScheduleSummary:
    """Test the generate_schedule_summary function."""

    def test_generate_schedule_summary_empty(self, monkeypatch) -> None:
        """Test generate schedule summary with empty schedule."""
        # Create a simple mock config object
        config = type('MockConfig', (), {
            'submissions': [],
            'conferences': [],
            'min_paper_lead_time_days': 60,
            'min_abstract_lead_time_days': 30
        })()
        
        empty_schedule: Dict[str, date] = {}
        
        result: ScheduleSummary = generate_schedule_summary(empty_schedule, config)  # type: ignore
        
        assert isinstance(result, ScheduleSummary)
        assert result.total_submissions == 0
        assert result.schedule_span == 0
        assert result.start_date is None
        assert result.end_date is None
        assert result.penalty_score == 0.0
        assert result.quality_score == 0.0
        assert result.efficiency_score == 0.0
        assert result.deadline_compliance == 100.0
        assert result.resource_utilization == 0.0

    def test_generate_schedule_summary_with_papers(self, monkeypatch) -> None:
        """Test generate schedule summary with papers."""
        # Mock the internal functions to avoid complex validation
        def mock_calculate_penalty_score(*args, **kwargs):
            mock_result = type('MockPenaltyResult', (), {
                'total_penalty': 0.0,
                'deadline_penalties': 0.0,
                'dependency_penalties': 0.0,
                'resource_penalties': 0.0
            })()
            return mock_result
        
        def mock_calculate_quality_score(*args, **kwargs):
            return 0.85
        
        def mock_calculate_efficiency_score(*args, **kwargs):
            return 0.78
        
        def mock_validate_deadline_constraints(*args, **kwargs):
            mock_result = type('MockDeadlineResult', (), {
                'compliance_rate': 100.0,
                'total_submissions': 2,
                'compliant_submissions': 2
            })()
            return mock_result
        
        def mock_validate_resources_constraints(*args, **kwargs):
            mock_result = type('MockResourceResult', (), {
                'max_observed': 1,
                'max_concurrent': 2,
                'total_days': 30
            })()
            return mock_result
        
        # Apply the mocks
        monkeypatch.setattr('src.generators.schedule.calculate_penalty_score', mock_calculate_penalty_score)
        monkeypatch.setattr('src.generators.schedule.calculate_quality_score', mock_calculate_quality_score)
        monkeypatch.setattr('src.generators.schedule.calculate_efficiency_score', mock_calculate_efficiency_score)
        monkeypatch.setattr('src.generators.schedule.validate_deadline_constraints', mock_validate_deadline_constraints)
        monkeypatch.setattr('src.generators.schedule.validate_resources_constraints', mock_validate_resources_constraints)
        
        # Create a simple mock config object
        config = type('MockConfig', (), {
            'submissions': [type('MockSubmission', (), {'id': 'paper1'})(), type('MockSubmission', (), {'id': 'paper2'})()],
            'conferences': []
        })()
        
        schedule: Dict[str, date] = {"paper1": date(2024, 1, 1)}
        
        result: ScheduleSummary = generate_schedule_summary(schedule, config)  # type: ignore
        
        assert isinstance(result, ScheduleSummary)
        assert result.total_submissions == 1  # Only paper1 is scheduled
        assert result.schedule_span >= 0
        assert result.start_date is not None
        assert result.penalty_score >= 0.0
        assert result.quality_score >= 0.0
        assert result.efficiency_score >= 0.0


class TestGenerateScheduleMetrics:
    """Test the generate_schedule_metrics function."""

    def test_generate_schedule_metrics_empty(self, monkeypatch) -> None:
        """Test generate schedule metrics with empty schedule."""
        # Create a simple mock config object
        config = type('MockConfig', (), {
            'submissions': [],
            'conferences': [],
            'min_paper_lead_time_days': 60,
            'min_abstract_lead_time_days': 30
        })()
        
        empty_schedule: Dict[str, date] = {}
        
        result: ScheduleMetrics = generate_schedule_metrics(empty_schedule, config)  # type: ignore
        
        assert isinstance(result, ScheduleMetrics)
        assert result.makespan == 0
        assert result.avg_utilization == 0.0
        assert result.peak_utilization == 0
        assert result.total_penalty == 0.0
        assert result.compliance_rate == 100.0
        assert result.quality_score == 0.0

    def test_generate_schedule_metrics_with_papers(self, monkeypatch) -> None:
        """Test generate schedule metrics with papers."""
        # Mock the internal functions to avoid complex validation
        def mock_calculate_penalty_score(*args, **kwargs):
            mock_result = type('MockPenaltyResult', (), {
                'total_penalty': 0.0,
                'deadline_penalties': 0.0,
                'dependency_penalties': 0.0,
                'resource_penalties': 0.0
            })()
            return mock_result
        
        def mock_validate_deadline_constraints(*args, **kwargs):
            mock_result = type('MockDeadlineResult', (), {
                'compliance_rate': 100.0,
                'total_submissions': 2,
                'compliant_submissions': 2
            })()
            return mock_result
        
        def mock_calculate_quality_score(*args, **kwargs):
            return 0.85
        
        # Apply the mocks
        monkeypatch.setattr('src.generators.schedule.calculate_penalty_score', mock_calculate_penalty_score)
        monkeypatch.setattr('src.generators.schedule.validate_deadline_constraints', mock_validate_deadline_constraints)
        monkeypatch.setattr('src.generators.schedule.calculate_quality_score', mock_calculate_quality_score)
        
        # Create a simple mock config object
        config = type('MockConfig', (), {
            'submissions': [
                type('MockSubmission', (), {'id': 'paper1', 'kind': 'paper'})(),
                type('MockSubmission', (), {'id': 'paper2', 'kind': 'paper'})()
            ],
            'conferences': [],
            'min_paper_lead_time_days': 60,
            'min_abstract_lead_time_days': 30
        })()
        
        # Create mock submissions with required attributes
        mock_submission1 = type('MockSubmission', (), {
            'id': 'paper1', 
            'kind': 'paper',
            'draft_window_months': 3
        })()
        mock_submission2 = type('MockSubmission', (), {
            'id': 'paper2', 
            'kind': 'paper',
            'draft_window_months': 2
        })()
        
        # Update config submissions with proper mock objects
        config.submissions = [mock_submission1, mock_submission2]
        
        schedule: Dict[str, date] = {"paper1": date(2024, 1, 1)}
        
        result: ScheduleMetrics = generate_schedule_metrics(schedule, config)  # type: ignore
        
        assert isinstance(result, ScheduleMetrics)
        assert result.makespan >= 0
        assert result.total_penalty >= 0.0
        assert result.compliance_rate >= 0.0
        assert result.quality_score >= 0.0
