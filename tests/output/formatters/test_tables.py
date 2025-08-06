"""Tests for output formatters tables module."""

from datetime import date
from unittest.mock import Mock

from output.formatters.tables import (
    format_schedule_table,
    format_metrics_table,
    format_deadline_table,
    save_schedule_json,
    save_table_csv,
    save_metrics_json
)


class TestFormatScheduleTable:
    """Test the format_schedule_table function."""

    def test_format_schedule_table_empty_schedule(self):
        """Test formatting empty schedule."""
        schedule = {}
        config = Mock(spec=Config)
        config.submissions = []
        
        result = format_schedule_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_schedule_table_with_papers(self):
        """Test formatting schedule with papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="ABSTRACT")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 0
        
        # Create mock schedule items
        item1 = Mock(spec=ScheduleItem)
        item1.paper = paper1
        item1.start_date = date(2024, 5, 1)
        item1.end_date = date(2024, 5, 15)
        
        item2 = Mock(spec=ScheduleItem)
        item2.paper = paper2
        item2.start_date = date(2024, 7, 1)
        item2.end_date = date(2024, 7, 20)
        
        # Create mock schedule
        schedule = Mock(spec=Schedule)
        schedule.items = [item1, item2]
        schedule.start_date = date(2024, 1, 1)
        schedule.end_date = date(2024, 12, 31)
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences_dict = {
            "conf1": Mock(name="Conference 1"),
            "conf2": Mock(name="Conference 2")
        }
        config.min_paper_lead_time_days = 90
        
        result = format_schedule_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check first row
        first_row = result[0]
        assert "Test Paper 1" in first_row.values()
        assert "2024-05-01" in first_row.values()
        assert "2024-05-15" in first_row.values()
        
        # Check second row
        second_row = result[1]
        assert "Test Paper 2" in second_row.values()
        assert "2024-07-01" in second_row.values()
        assert "2024-07-20" in second_row.values()

    def test_format_schedule_table_with_missing_data(self):
        """Test formatting schedule with missing data."""
        # Create mock paper with missing data
        paper = Mock(spec=Paper)
        paper.title = "Test Paper"
        paper.deadline = None
        paper.estimated_hours = None
        paper.kind = Mock(value="PAPER")
        paper.conference_id = None
        paper.draft_window_months = 3
        
        item = Mock(spec=ScheduleItem)
        item.paper = paper
        item.start_date = date(2024, 5, 1)
        item.end_date = date(2024, 5, 15)
        
        schedule = Mock(spec=Schedule)
        schedule.items = [item]
        
        config = Mock(spec=Config)
        config.submissions = [paper]
        config.conferences_dict = {}
        config.min_paper_lead_time_days = 90
        
        result = format_schedule_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 1
        
        row = result[0]
        assert "Test Paper" in row.values()
        assert "2024-05-01" in row.values()
        assert "2024-05-15" in row.values()


class TestFormatMetricsTable:
    """Test the format_metrics_table function."""

    def test_format_metrics_table_basic(self):
        """Test basic metrics table formatting."""
        metrics = Mock(spec=ScheduleSummary)
        metrics.total_submissions = 5
        metrics.schedule_span = 120
        metrics.penalty_score = 150.50
        metrics.quality_score = 0.85
        metrics.efficiency_score = 0.78
        metrics.deadline_compliance = 90.5
        metrics.resource_utilization = 0.75
        
        result = format_metrics_table(metrics)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check that key metrics are present
        metric_values = [str(v) for row in result for v in row.values()]
        assert "5" in metric_values  # total_submissions
        assert "120" in metric_values  # schedule_span
        assert "150.50" in metric_values or "150.5" in metric_values  # penalty_score

    def test_format_metrics_table_with_none_values(self):
        """Test metrics table formatting with None values."""
        metrics = Mock(spec=ScheduleSummary)
        metrics.total_submissions = None
        metrics.schedule_span = None
        metrics.penalty_score = None
        metrics.quality_score = None
        metrics.efficiency_score = None
        metrics.deadline_compliance = None
        metrics.resource_utilization = None
        
        result = format_metrics_table(metrics)
        
        assert isinstance(result, list)
        # Should still create a table even with None values
        assert len(result) > 0

    def test_format_metrics_table_empty(self):
        """Test metrics table formatting with empty metrics."""
        metrics = Mock(spec=ScheduleSummary)
        # Don't set any attributes
        
        result = format_metrics_table(metrics)
        
        assert isinstance(result, list)
        # Should handle missing attributes gracefully


class TestFormatDeadlineTable:
    """Test the format_deadline_table function."""

    def test_format_deadline_table_empty_schedule(self):
        """Test formatting empty schedule for deadlines."""
        schedule = {}
        config = Mock(spec=Config)
        config.submissions = []
        
        result = format_deadline_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_format_deadline_table_with_papers(self):
        """Test formatting deadline table with papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        paper1.kind = Mock(value="PAPER")
        paper1.conference_id = "conf1"
        paper1.draft_window_months = 3
        
        paper2 = Mock(spec=Paper)
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        paper2.kind = Mock(value="ABSTRACT")
        paper2.conference_id = "conf2"
        paper2.draft_window_months = 0
        
        # Create mock schedule items
        item1 = Mock(spec=ScheduleItem)
        item1.paper = paper1
        item1.start_date = date(2024, 5, 1)
        item1.end_date = date(2024, 5, 15)
        
        item2 = Mock(spec=ScheduleItem)
        item2.paper = paper2
        item2.start_date = date(2024, 7, 1)
        item2.end_date = date(2024, 7, 20)
        
        # Create mock schedule
        schedule = Mock(spec=Schedule)
        schedule.items = [item1, item2]
        
        config = Mock(spec=Config)
        config.submissions = [paper1, paper2]
        config.conferences_dict = {
            "conf1": Mock(name="Conference 1", deadlines={"PAPER": date(2024, 6, 1)}),
            "conf2": Mock(name="Conference 2", deadlines={"ABSTRACT": date(2024, 8, 1)})
        }
        config.min_paper_lead_time_days = 90
        
        result = format_deadline_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Check first row
        first_row = result[0]
        assert "Test Paper 1" in first_row.values()
        assert "2024-06-01" in first_row.values()  # deadline
        assert "2024-05-15" in first_row.values()  # end_date
        
        # Check second row
        second_row = result[1]
        assert "Test Paper 2" in second_row.values()
        assert "2024-08-01" in second_row.values()  # deadline
        assert "2024-07-20" in second_row.values()  # end_date

    def test_format_deadline_table_with_late_submissions(self):
        """Test deadline table with submissions that are late."""
        # Create mock paper with late submission
        paper = Mock(spec=Paper)
        paper.title = "Late Paper"
        paper.deadline = date(2024, 6, 1)
        paper.estimated_hours = 40
        paper.kind = Mock(value="PAPER")
        paper.conference_id = "conf1"
        paper.draft_window_months = 3
        
        item = Mock(spec=ScheduleItem)
        item.paper = paper
        item.start_date = date(2024, 5, 1)
        item.end_date = date(2024, 6, 15)  # After deadline
        
        schedule = Mock(spec=Schedule)
        schedule.items = [item]
        
        config = Mock(spec=Config)
        config.submissions = [paper]
        config.conferences_dict = {
            "conf1": Mock(name="Conference 1", deadlines={"PAPER": date(2024, 6, 1)})
        }
        config.min_paper_lead_time_days = 90
        
        result = format_deadline_table(schedule, config)
        
        assert isinstance(result, list)
        assert len(result) == 1
        
        row = result[0]
        assert "Late Paper" in row.values()
        assert "2024-06-01" in row.values()  # deadline
        assert "2024-06-15" in row.values()  # end_date


class TestSaveScheduleJson:
    """Test the save_schedule_json function."""

    def test_save_schedule_json_basic(self, tmp_path):
        """Test basic schedule JSON saving."""
        schedule = {"paper1": "2024-01-01", "paper2": "2024-02-01"}
        output_dir = str(tmp_path)
        
        result = save_schedule_json(schedule, output_dir)
        
        assert isinstance(result, str)
        assert result.endswith("schedule.json")
        assert "schedule.json" in result

    def test_save_schedule_json_custom_filename(self, tmp_path):
        """Test schedule JSON saving with custom filename."""
        schedule = {"paper1": "2024-01-01"}
        output_dir = str(tmp_path)
        
        result = save_schedule_json(schedule, output_dir, "custom_schedule.json")
        
        assert isinstance(result, str)
        assert result.endswith("custom_schedule.json")


class TestSaveTableCsv:
    """Test the save_table_csv function."""

    def test_save_table_csv_basic(self, tmp_path):
        """Test basic table CSV saving."""
        table_data = [
            {"Month": "2024-01", "Papers": "2", "Deadlines": "1"},
            {"Month": "2024-02", "Papers": "1", "Deadlines": "0"}
        ]
        output_dir = str(tmp_path)
        
        result = save_table_csv(table_data, output_dir, "test_table.csv")
        
        assert isinstance(result, str)
        assert result.endswith("test_table.csv")

    def test_save_table_csv_empty(self, tmp_path):
        """Test table CSV saving with empty data."""
        table_data = []
        output_dir = str(tmp_path)
        
        result = save_table_csv(table_data, output_dir, "empty_table.csv")
        
        assert result == ""


class TestSaveMetricsJson:
    """Test the save_metrics_json function."""

    def test_save_metrics_json_basic(self, tmp_path):
        """Test basic metrics JSON saving."""
        metrics = Mock(spec=ScheduleSummary)
        metrics.total_submissions = 5
        metrics.schedule_span = 120
        metrics.penalty_score = 150.50
        metrics.quality_score = 0.85
        metrics.efficiency_score = 0.78
        metrics.deadline_compliance = 90.5
        metrics.resource_utilization = 0.75
        
        output_dir = str(tmp_path)
        
        result = save_metrics_json(metrics, output_dir)
        
        assert isinstance(result, str)
        assert result.endswith("metrics.json")

    def test_save_metrics_json_custom_filename(self, tmp_path):
        """Test metrics JSON saving with custom filename."""
        metrics = Mock(spec=ScheduleSummary)
        output_dir = str(tmp_path)
        
        result = save_metrics_json(metrics, output_dir, "custom_metrics.json")
        
        assert isinstance(result, str)
        assert result.endswith("custom_metrics.json")


class TestGetOutputSummary:
    """Test the get_output_summary function."""

    def test_get_output_summary_basic(self):
        """Test basic output summary generation."""
        saved_files = {
            "schedule": "/path/to/schedule.json",
            "metrics": "/path/to/metrics.json",
            "table": "/path/to/table.csv"
        }
        
        result = get_output_summary(saved_files)
        
        assert isinstance(result, str)
        assert "Output files saved" in result
        assert "schedule.json" in result
        assert "metrics.json" in result
        assert "table.csv" in result

    def test_get_output_summary_empty(self):
        """Test output summary with empty files dict."""
        saved_files = {}
        
        result = get_output_summary(saved_files)
        
        assert isinstance(result, str)
        assert "No files were saved" in result

    def test_get_output_summary_with_empty_paths(self):
        """Test output summary with empty file paths."""
        saved_files = {
            "schedule": "",
            "metrics": None,
            "table": "/path/to/table.csv"
        }
        
        result = get_output_summary(saved_files)
        
        assert isinstance(result, str)
        assert "Output files saved" in result
        assert "table.csv" in result
