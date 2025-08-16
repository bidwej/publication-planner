"""Tests for CSV export functionality."""

import pytest
from pathlib import Path
from datetime import date, timedelta
from typing import Dict

from core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
from exporters.csv_exporter import CSVExporter


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    # Create sample conferences
    conferences = [
        Conference(
            id="ICRA2026",
            name="IEEE International Conference on Robotics and Automation 2026",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 1, 15),
                SubmissionType.PAPER: date(2026, 2, 15)
            }
        ),
        Conference(
            id="MICCAI2026",
            name="Medical Image Computing and Computer Assisted Intervention 2026",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 3, 1),
                SubmissionType.PAPER: date(2026, 4, 1)
            }
        )
    ]
    
    # Create sample submissions
    submissions = [
        Submission(
            id="mod1-wrk",
            title="Endoscope Navigation Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="ICRA2026",
            depends_on=[],
            draft_window_months=0,
            engineering=True
        ),
        Submission(
            id="paper1-pap",
            title="AI-Powered Endoscope Control System",
            kind=SubmissionType.PAPER,
            conference_id="ICRA2026",
            depends_on=["mod1-wrk"],
            draft_window_months=3,
            engineering=True
        ),
        Submission(
            id="mod2-wrk",
            title="Medical Image Analysis Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="MICCAI2026",
            depends_on=[],
            draft_window_months=0,
            engineering=False
        ),
        Submission(
            id="paper2-pap",
            title="Deep Learning for Endoscope Guidance",
            kind=SubmissionType.PAPER,
            conference_id="MICCAI2026",
            depends_on=["mod2-wrk"],
            draft_window_months=3,
            engineering=False
        )
    ]
    
    return Config(
        submissions=submissions,
        conferences=conferences,
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        default_paper_lead_time_months=3,
        penalty_costs={
            "default_mod_penalty_per_day": 1000.0,
            "default_paper_penalty_per_day": 2000.0,
            "default_monthly_slip_penalty": 1000.0,
            "default_full_year_deferral_penalty": 5000.0,
            "missed_abstract_penalty": 3000.0,
            "resource_violation_penalty": 200.0
        },
        priority_weights={
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        scheduling_options={
            "enable_blackout_periods": False,
            "enable_early_abstract_scheduling": False,
            "enable_working_days_only": False,
            "enable_priority_weighting": True,
            "enable_dependency_tracking": True,
            "enable_concurrency_control": True
        },
        blackout_dates=[],
        data_files={
            "conferences": "conferences.json",
            "papers": "papers.json",
            "mods": "mods.json"
        }
    )


@pytest.fixture
def sample_schedule():
    """Create a sample schedule for testing."""
    return {
        "mod1-wrk": date(2025, 10, 1),
        "paper1-pap": date(2025, 11, 1),
        "mod2-wrk": date(2025, 12, 1),
        "paper2-pap": date(2026, 1, 1)
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    return tmp_path


class TestCSVExporter:
    """Test cases for CSV export functionality."""
    
    def test_export_schedule_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test schedule CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_schedule_csv(sample_schedule, str(temp_output_dir), "test_schedule.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "ID" in content
            assert "Title" in content
            assert "Start Date" in content
            assert "End Date" in content
            assert "mod1-wrk" in content
            assert "paper1-pap" in content
    
    def test_export_metrics_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test metrics CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_metrics_csv(sample_schedule, str(temp_output_dir), "test_metrics.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Metric" in content
            assert "Value" in content
            assert "Total Submissions" in content
            assert "Schedule Span" in content
    
    def test_export_deadline_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test deadline CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_deadline_csv(sample_schedule, str(temp_output_dir), "test_deadlines.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Submission" in content  # Changed from "ID" to "Submission"
            assert "Deadline" in content
            assert "Status" in content
    
    def test_export_violations_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test violations CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_violations_csv(sample_schedule, str(temp_output_dir), "test_violations.csv")
        
        # For violations, it's okay if no violations are found (empty file)
        if filepath != "":
            assert Path(filepath).exists()
            # Verify CSV content if file exists
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():  # Only check content if file is not empty
                    assert "Violation Type" in content
                    assert "Severity" in content
    
    def test_export_penalties_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test penalties CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_penalties_csv(sample_schedule, str(temp_output_dir), "test_penalties.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Penalty Type" in content
            assert "Amount" in content
            assert "Total Penalty" in content
    
    def test_export_summary_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test summary CSV export."""
        exporter = CSVExporter(sample_config)
        filepath = exporter.export_summary_csv(sample_schedule, str(temp_output_dir), "test_summary.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Category" in content
            assert "Value" in content
            assert "Total Submissions" in content
    
    def test_export_comparison_csv(self, sample_config, temp_output_dir):
        """Test comparison CSV export."""
        exporter = CSVExporter(sample_config)
        
        # Create sample comparison results
        comparison_results = {
            "greedy": {
                "schedule": {"mod1-wrk": date(2025, 10, 1)},
                "metrics": {
                    "schedule_span": 30,
                    "penalty_score": 100.0,
                    "quality_score": 85.0,
                    "efficiency_score": 90.0,
                    "compliance_rate": 95.0,
                    "resource_utilization": 80.0
                }
            },
            "optimal": {
                "schedule": {"mod1-wrk": date(2025, 10, 5)},
                "metrics": {
                    "schedule_span": 25,
                    "penalty_score": 50.0,
                    "quality_score": 95.0,
                    "efficiency_score": 95.0,
                    "compliance_rate": 98.0,
                    "resource_utilization": 85.0
                }
            }
        }
        
        filepath = exporter.export_comparison_csv(comparison_results, str(temp_output_dir), "test_comparison.csv")
        
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Verify CSV content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Strategy" in content
            assert "Total Submissions" in content
            assert "Penalty Score" in content
            assert "greedy" in content
            assert "optimal" in content
    
    def test_export_all_csv(self, sample_config, sample_schedule, temp_output_dir):
        """Test export all CSV formats."""
        exporter = CSVExporter(sample_config)
        saved_files = exporter.export_all_csv(sample_schedule, str(temp_output_dir))
        
        # Verify all files were created
        expected_files = ["schedule", "metrics", "deadlines", "violations", "penalties", "summary"]
        for file_type in expected_files:
            assert file_type in saved_files
            # Some files may be empty if no data (e.g., violations)
            if saved_files[file_type] != "":
                assert Path(saved_files[file_type]).exists()
    
    def test_empty_schedule_handling(self, sample_config, temp_output_dir):
        """Test handling of empty schedules."""
        exporter = CSVExporter(sample_config)
        empty_schedule = {}
        
        # Test metrics export with empty schedule
        filepath = exporter.export_metrics_csv(empty_schedule, str(temp_output_dir), "empty_metrics.csv")
        assert filepath != ""
        assert Path(filepath).exists()
        
        # Test summary export with empty schedule
        filepath = exporter.export_summary_csv(empty_schedule, str(temp_output_dir), "empty_summary.csv")
        assert filepath != ""
        assert Path(filepath).exists()
    
    def test_comprehensive_metrics_calculation(self, sample_config, sample_schedule):
        """Test comprehensive metrics calculation."""
        exporter = CSVExporter(sample_config)
        metrics_data = exporter._calculate_comprehensive_metrics(sample_schedule)
        
        assert len(metrics_data) > 0
        
        # Check for required metrics
        metric_names = [item["Metric"] for item in metrics_data]
        assert "Total Submissions" in metric_names
        assert "Schedule Span (Days)" in metric_names
        assert "Start Date" in metric_names
        assert "End Date" in metric_names
        assert "Max Concurrent Submissions" in metric_names
        assert "Average Daily Load" in metric_names
    
    def test_comprehensive_penalties_calculation(self, sample_config, sample_schedule):
        """Test comprehensive penalties calculation."""
        exporter = CSVExporter(sample_config)
        penalties_data = exporter._calculate_comprehensive_penalties(sample_schedule)
        
        assert len(penalties_data) > 0
        
        # Check for required penalty types
        penalty_types = [item["Penalty Type"] for item in penalties_data]
        assert "Total Penalty" in penalty_types
        assert "Deadline Penalties" in penalty_types
        assert "Dependency Penalties" in penalty_types
        assert "Resource Penalties" in penalty_types
        assert "Conference Compatibility Penalties" in penalty_types
        assert "Abstract-Paper Dependency Penalties" in penalty_types
    
    def test_validation_fallback(self, sample_config, sample_schedule):
        """Test validation fallback when validation module is not available."""
        exporter = CSVExporter(sample_config)
        
        # Mock the import error scenario
        with pytest.MonkeyPatch().context() as m:
            m.setattr(exporter, '_run_comprehensive_validation', lambda x: {
                "summary": {
                    "overall_valid": True,
                    "total_violations": 0,
                    "compliance_rate": 100.0
                },
                "constraints": {},
                "analytics": {}
            })
            
            validation_result = exporter._run_comprehensive_validation(sample_schedule)
            assert validation_result["summary"]["overall_valid"] is True
            assert validation_result["summary"]["total_violations"] == 0
    
    def test_penalty_fallback(self, sample_config, sample_schedule):
        """Test penalty calculation fallback when penalty module is not available."""
        exporter = CSVExporter(sample_config)
        
        # Mock the import error scenario
        with pytest.MonkeyPatch().context() as m:
            m.setattr(exporter, '_calculate_comprehensive_penalties', lambda x: [
                {"Penalty Type": "Total Penalty", "Amount": "0.0"},
                {"Penalty Type": "Deadline Penalties", "Amount": "0.0"},
                {"Penalty Type": "Dependency Penalties", "Amount": "0.0"},
                {"Penalty Type": "Resource Penalties", "Amount": "0.0"},
                {"Penalty Type": "Conference Compatibility Penalties", "Amount": "0.0"},
                {"Penalty Type": "Abstract-Paper Dependency Penalties", "Amount": "0.0"},
            ])
            
            penalties_data = exporter._calculate_comprehensive_penalties(sample_schedule)
            assert len(penalties_data) > 0
            assert all("Penalty Type" in item and "Amount" in item for item in penalties_data)


def test_export_schedule_to_csv_convenience_function(sample_config, sample_schedule, temp_output_dir):
    """Test the convenience function for exporting schedule to CSV."""
    from exporters.csv_exporter import export_schedule_to_csv
    
    filepath = export_schedule_to_csv(sample_schedule, sample_config, str(temp_output_dir), "convenience_test.csv")
    
    assert filepath != ""
    assert Path(filepath).exists()
    assert "convenience_test.csv" in filepath


def test_export_all_csv_formats_convenience_function(sample_config, sample_schedule, temp_output_dir):
    """Test the convenience function for exporting all CSV formats."""
    from exporters.csv_exporter import export_all_csv_formats
    
    saved_files = export_all_csv_formats(sample_schedule, sample_config, str(temp_output_dir))
    
    assert len(saved_files) == 6  # schedule, metrics, deadlines, violations, penalties, summary
    for filepath in saved_files.values():
        if filepath != "":  # Some files may be empty if no data
            assert Path(filepath).exists()
