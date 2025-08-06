"""Tests for the generators schedule module."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch
import os

from core.models import Config, ScheduleSummary, ScheduleMetrics
from output.generators.schedule import (
    create_output_directory, save_all_outputs, 
    generate_schedule_summary, generate_schedule_metrics
)


class TestCreateOutputDirectory:
    """Test the create_output_directory function."""

    def test_create_output_directory_basic(self, tmp_path):
        """Test basic directory creation."""
        base_dir = str(tmp_path)
        output_dir = create_output_directory(base_dir)
        
        assert output_dir.startswith(base_dir)
        assert "output_" in output_dir
        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)

    def test_create_output_directory_default(self, tmp_path):
        """Test directory creation with default base_dir."""
        with patch('output.generators.schedule.os.path.join') as mock_join, \
             patch('output.generators.schedule.os.makedirs') as mock_makedirs:
            
            mock_join.return_value = "/test/output_20240101_120000"
            
            output_dir = create_output_directory()
            
            mock_join.assert_called_once()
            mock_makedirs.assert_called_once_with("/test/output_20240101_120000", exist_ok=True)
            assert output_dir == "/test/output_20240101_120000"


class TestSaveAllOutputs:
    """Test the save_all_outputs function."""

    def test_save_all_outputs_basic(self, tmp_path):
        """Test basic save all outputs functionality."""
        schedule = {"paper1": "2024-01-01", "paper2": "2024-02-01"}
        schedule_table = [{"Month": "2024-01", "Papers": "1"}]
        metrics_table = [{"Metric": "Total", "Value": "2"}]
        deadline_table = [{"Conference": "Test", "Deadline": "2024-01-15"}]
        
        metrics = Mock(spec=ScheduleSummary)
        metrics.total_submissions = 2
        metrics.schedule_span = 30
        metrics.penalty_score = 0.0
        metrics.quality_score = 85.0
        metrics.efficiency_score = 75.0
        metrics.deadline_compliance = 100.0
        metrics.resource_utilization = 80.0
        
        output_dir = str(tmp_path)
        
        with patch('output.generators.schedule.save_schedule_json') as mock_save_schedule, \
             patch('output.generators.schedule.save_table_csv') as mock_save_csv, \
             patch('output.generators.schedule.save_metrics_json') as mock_save_metrics:
            
            mock_save_schedule.return_value = "/test/schedule.json"
            mock_save_csv.return_value = "/test/table.csv"
            mock_save_metrics.return_value = "/test/metrics.json"
            
            result = save_all_outputs(schedule, schedule_table, metrics_table, deadline_table, metrics, output_dir)
            
            assert isinstance(result, dict)
            assert "schedule" in result
            assert "schedule_table" in result
            assert "metrics_table" in result
            assert "deadline_table" in result
            assert "metrics" in result

    def test_save_all_outputs_empty_tables(self, tmp_path):
        """Test save all outputs with empty tables."""
        schedule = {"paper1": "2024-01-01"}
        schedule_table = []
        metrics_table = []
        deadline_table = []
        
        metrics = Mock(spec=ScheduleSummary)
        
        output_dir = str(tmp_path)
        
        with patch('output.generators.schedule.save_schedule_json') as mock_save_schedule, \
             patch('output.generators.schedule.save_table_csv') as mock_save_csv, \
             patch('output.generators.schedule.save_metrics_json') as mock_save_metrics:
            
            mock_save_schedule.return_value = "/test/schedule.json"
            mock_save_metrics.return_value = "/test/metrics.json"
            
            result = save_all_outputs(schedule, schedule_table, metrics_table, deadline_table, metrics, output_dir)
            
            assert isinstance(result, dict)
            assert "schedule" in result
            assert "metrics" in result
            # Empty tables should not be saved
            assert "schedule_table" not in result
            assert "metrics_table" not in result
            assert "deadline_table" not in result


class TestGenerateScheduleSummary:
    """Test the generate_schedule_summary function."""

    def test_generate_schedule_summary_empty(self):
        """Test summary generation with empty schedule."""
        schedule = {}
        config = Mock(spec=Config)
        config.submissions = []
        
        result = generate_schedule_summary(schedule, config)
        
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

    def test_generate_schedule_summary_with_papers(self):
        """Test summary generation with papers."""
        schedule = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        config = Mock(spec=Config)
        config.submissions = [Mock(), Mock()]
        
        with patch('output.generators.schedule.calculate_penalty_score') as mock_penalty, \
             patch('output.generators.schedule.calculate_quality_score') as mock_quality, \
             patch('output.generators.schedule.calculate_efficiency_score') as mock_efficiency, \
             patch('output.generators.schedule.validate_deadline_compliance') as mock_deadline, \
             patch('output.generators.schedule.validate_resource_constraints') as mock_resource:
            
            mock_penalty.return_value = Mock(total_penalty=150.0)
            mock_quality.return_value = 0.85
            mock_efficiency.return_value = 0.78
            mock_deadline.return_value = Mock(compliance_rate=90.0)
            mock_resource.return_value = Mock(max_observed=3, max_concurrent=4)
            
            result = generate_schedule_summary(schedule, config)
            
            assert isinstance(result, ScheduleSummary)
            assert result.total_submissions == 2
            assert result.schedule_span == 61  # (2024-07-01) - (2024-05-01) = 61 days
            assert result.start_date == date(2024, 5, 1)
            assert result.end_date == date(2024, 7, 1)
            assert result.penalty_score == 150.0
            assert result.quality_score == 0.85
            assert result.efficiency_score == 0.78
            assert result.deadline_compliance == 90.0
            assert result.resource_utilization == 0.75  # 3/4


class TestGenerateScheduleMetrics:
    """Test the generate_schedule_metrics function."""

    def test_generate_schedule_metrics_empty(self):
        """Test metrics generation with empty schedule."""
        schedule = {}
        config = Mock(spec=Config)
        config.submissions = []
        
        result = generate_schedule_metrics(schedule, config)
        
        assert isinstance(result, ScheduleMetrics)
        assert result.makespan == 0
        assert result.avg_utilization == 0.0
        assert result.peak_utilization == 0
        assert result.total_penalty == 0.0
        assert result.compliance_rate == 100.0
        assert result.quality_score == 0.0

    def test_generate_schedule_metrics_with_papers(self):
        """Test metrics generation with papers."""
        schedule = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        # Create mock submissions
        paper1 = Mock()
        paper1.id = "paper1"
        paper1.kind = Mock(value="PAPER")
        paper1.draft_window_months = 3
        
        paper2 = Mock()
        paper2.id = "paper2"
        paper2.kind = Mock(value="PAPER")
        paper2.draft_window_months = 2
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.min_paper_lead_time_days = 90
        
        with patch('output.generators.schedule.calculate_penalty_score') as mock_penalty, \
             patch('output.generators.schedule.validate_deadline_compliance') as mock_deadline, \
             patch('output.generators.schedule.calculate_quality_score') as mock_quality:
            
            mock_penalty.return_value = Mock(total_penalty=150.0)
            mock_deadline.return_value = Mock(compliance_rate=90.0)
            mock_quality.return_value = 0.85
            
            result = generate_schedule_metrics(schedule, config)
            
            assert isinstance(result, ScheduleMetrics)
            assert result.makespan == 61  # (2024-07-01) - (2024-05-01) = 61 days
            assert result.total_penalty == 150.0
            assert result.compliance_rate == 90.0
            assert result.quality_score == 0.85
