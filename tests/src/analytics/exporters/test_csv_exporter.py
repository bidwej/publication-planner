"""Tests for CSV export functionality."""

from datetime import date
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest

from src.analytics.exporters.csv_exporter import CSVExporter, export_schedule_to_csv, export_all_csv_formats
from src.core.models import Config, ScheduleSummary, ScheduleMetrics, SubmissionType


class TestCSVExporter:
    """Test the CSVExporter class."""
    
    def test_csv_exporter_initialization(self, sample_config) -> None:
        """Test CSVExporter initialization."""
        exporter = CSVExporter(sample_config)
        assert exporter.config == sample_config
    
    def test_export_schedule_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic schedule CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_schedule_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"
        
        # Check file contents
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "ID" in content
            assert "Start Date" in content
    
    def test_export_schedule_csv_empty_schedule(self, sample_config, tmp_path) -> None:
        """Test schedule CSV export with empty schedule."""
        schedule: Dict[str, date] = {}
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_schedule_csv(schedule, str(tmp_path))
        
        # Should return empty string for empty schedule
        assert result == ""
    
    def test_export_metrics_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic metrics CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_metrics_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"
        
        # Check file contents
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Metric" in content
            assert "Value" in content
            assert "Total Submissions" in content
    
    def test_export_metrics_csv_empty_schedule(self, sample_config, tmp_path) -> None:
        """Test metrics CSV export with empty schedule."""
        schedule: Dict[str, date] = {}
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_metrics_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        
        # Check file contents for empty schedule
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Total Submissions" in content
            assert "0" in content
    
    def test_export_deadline_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic deadline CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_deadline_csv(schedule, str(tmp_path))
        
        # May return empty string if no deadlines configured
        if result:
            assert Path(result).exists()
            assert Path(result).suffix == ".csv"
    
    def test_export_violations_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic violations CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_violations_csv(schedule, str(tmp_path))
        
        # May return empty string if no violations
        if result:
            assert Path(result).exists()
            assert Path(result).suffix == ".csv"
    
    def test_export_penalties_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic penalties CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_penalties_csv(schedule, str(tmp_path))
        
        # May return empty string if no penalties
        if result:
            assert Path(result).exists()
            assert Path(result).suffix == ".csv"
    
    def test_export_comparison_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic comparison CSV export."""
        comparison_results = {
            "greedy": {
                "schedule": {"paper1": date(2024, 5, 1)},
                "metrics": {
                    "schedule_span": 30,
                    "penalty_score": 100.0,
                    "quality_score": 0.8,
                    "efficiency_score": 0.7,
                    "compliance_rate": 90.0,
                    "resource_utilization": 75.0
                }
            },
            "stochastic": {
                "schedule": {"paper2": date(2024, 6, 1)},
                "metrics": {
                    "schedule_span": 45,
                    "penalty_score": 150.0,
                    "quality_score": 0.75,
                    "efficiency_score": 0.65,
                    "compliance_rate": 85.0,
                    "resource_utilization": 80.0
                }
            }
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_comparison_csv(comparison_results, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"
        
        # Check file contents
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Strategy" in content
            assert "greedy" in content
            assert "stochastic" in content
    
    def test_export_summary_csv_basic(self, sample_config, tmp_path) -> None:
        """Test basic summary CSV export."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_summary_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"
        
        # Check file contents
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Category" in content
            assert "Value" in content
            assert "Total Submissions" in content
    
    def test_export_summary_csv_empty_schedule(self, sample_config, tmp_path) -> None:
        """Test summary CSV export with empty schedule."""
        schedule: Dict[str, date] = {}
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_summary_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        
        # Check file contents for empty schedule
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Status" in content
            assert "No Schedule" in content
    
    def test_export_all_csv_basic(self, sample_config, tmp_path) -> None:
        """Test export all CSV formats."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_all_csv(schedule, str(tmp_path))
        
        assert isinstance(result, dict)
        expected_keys = ["schedule", "metrics", "deadlines", "violations", "penalties", "summary"]
        
        for key in expected_keys:
            if key in result and result[key]:
                assert Path(result[key]).exists()
                assert Path(result[key]).suffix == ".csv"
    
    def test_export_all_csv_empty_schedule(self, sample_config, tmp_path) -> None:
        """Test export all CSV formats with empty schedule."""
        schedule: Dict[str, date] = {}
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_all_csv(schedule, str(tmp_path))
        
        assert isinstance(result, dict)
        # Should still create metrics and summary files
        if "metrics" in result and result["metrics"]:
            assert Path(result["metrics"]).exists()
        if "summary" in result and result["summary"]:
            assert Path(result["summary"]).exists()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_export_schedule_to_csv(self, sample_config, tmp_path) -> None:
        """Test export_schedule_to_csv convenience function."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        result: Any = export_schedule_to_csv(schedule, sample_config, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"
    
    def test_export_all_csv_formats(self, sample_config, tmp_path) -> None:
        """Test export_all_csv_formats convenience function."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        result: Any = export_all_csv_formats(schedule, sample_config, str(tmp_path))
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Check that at least some files were created
        created_files = [path for path in result.values() if path]
        assert len(created_files) > 0
        
        for filepath in created_files:
            assert Path(filepath).exists()
            assert Path(filepath).suffix == ".csv"


class TestCSVExporterEdgeCases:
    """Test edge cases and error handling."""
    
    def test_csv_exporter_with_nonexistent_directory(self, sample_config) -> None:
        """Test CSV export with nonexistent directory."""
        schedule: Dict[str, date] = {"paper1": date(2024, 5, 1)}
        exporter = CSVExporter(sample_config)
        
        # Should create directory automatically
        result: Any = exporter.export_schedule_csv(schedule, "/tmp/nonexistent/dir")
        
        # Should still work (creates directory)
        assert result
        assert Path(result).exists()
    
    def test_csv_exporter_with_special_characters(self, sample_config, tmp_path) -> None:
        """Test CSV export with special characters in data."""
        schedule: Dict[str, date] = {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1)
        }
        
        # Mock submission with special characters
        mock_submission = Mock()
        mock_submission.title = "Paper with 'quotes' and \"double quotes\""
        mock_submission.kind = Mock(value="PAPER")
        mock_submission.conference_id = "conf_with_special_chars"
        
        sample_config.submissions_dict = {
            "paper1": mock_submission,
            "paper2": mock_submission
        }
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_schedule_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        
        # Check that file can be read without encoding errors
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "paper1" in content
    
    def test_csv_exporter_with_large_dataset(self, sample_config, tmp_path) -> None:
        """Test CSV export with large dataset."""
        # Create large schedule
        schedule: Dict[str, date] = {}
        for i in range(100):
            schedule[f"paper{i}"] = date(2024, 5, 1 + i)
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_schedule_csv(schedule, str(tmp_path))
        
        assert result
        assert Path(result).exists()
        
        # Check file size
        file_size = Path(result).stat().st_size
        assert file_size > 0
    
    def test_csv_exporter_custom_filename(self, sample_config, tmp_path) -> None:
        """Test CSV export with custom filename."""
        schedule: Dict[str, date] = {"paper1": date(2024, 5, 1)}
        
        exporter = CSVExporter(sample_config)
        result: Any = exporter.export_schedule_csv(schedule, str(tmp_path), "custom_schedule.csv")
        
        assert result
        assert Path(result).name == "custom_schedule.csv"
        assert Path(result).exists()
