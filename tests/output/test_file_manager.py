"""Tests for output file manager module."""

import pytest
import tempfile
import os
from datetime import date
from typing import Dict
from src.output.file_manager import (
    create_output_directory, save_schedule_json, save_table_csv,
    save_metrics_json, save_all_outputs, get_output_summary
)
from src.core.models import Config


class TestFileManager:
    """Test file manager functionality."""
    
    def test_create_output_directory(self):
        """Test output directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = create_output_directory(temp_dir)
            
            # Directory should exist
            assert os.path.exists(output_dir)
            assert os.path.isdir(output_dir)
            assert "output_" in output_dir
    
    def test_save_schedule_json(self):
        """Test saving schedule as JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schedule = {
                "paper1": "2025-01-01",
                "paper2": "2025-02-01"
            }
            
            filepath = save_schedule_json(schedule, temp_dir)
            
            # File should exist
            assert os.path.exists(filepath)
            assert filepath.endswith("schedule.json")
    
    def test_save_table_csv(self):
        """Test saving table as CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            table_data = [
                {"Month": "2025-01", "Papers": "2", "Deadlines": "1"},
                {"Month": "2025-02", "Papers": "1", "Deadlines": "0"}
            ]
            
            filepath = save_table_csv(table_data, temp_dir, "test_table.csv")
            
            # File should exist
            assert os.path.exists(filepath)
            assert filepath.endswith("test_table.csv")
    
    def test_save_all_outputs(self):
        """Test saving all outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            schedule = {"paper1": "2025-01-01"}
            schedule_table = [{"Month": "2025-01", "Papers": "1"}]
            metrics_table = [{"Metric": "Total", "Value": "1"}]
            deadline_table = [{"Conference": "Test", "Deadline": "2025-01-15"}]
            
            # Create a simple metrics object
            from src.core.models import ScheduleSummary
            metrics = ScheduleSummary(
                total_submissions=1,
                schedule_span=30,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 30),
                penalty_score=0.0,
                quality_score=85.0,
                efficiency_score=75.0,
                deadline_compliance=100.0,
                resource_utilization=80.0
            )
            
            saved_files = save_all_outputs(
                schedule, schedule_table, metrics_table, deadline_table, metrics, temp_dir
            )
            
            # Should have saved files
            assert isinstance(saved_files, dict)
            assert len(saved_files) > 0
    
    def test_get_output_summary(self):
        """Test output summary generation."""
        saved_files = {
            "schedule": "/path/to/schedule.json",
            "metrics": "/path/to/metrics.json"
        }
        
        summary = get_output_summary(saved_files)
        
        assert isinstance(summary, str)
        assert "Output files saved" in summary
