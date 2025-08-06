"""Tests for generate planner module."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from src.output.generate_planner import GeneratePlanner
from src.core.models import Config, CompleteOutput, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence


class TestGeneratePlanner:
    """Test the GeneratePlanner class."""
    
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
    def sample_schedule(self):
        """Provide a sample schedule for testing."""
        return {
            "J1-pap": date(2024, 11, 1)
        }
    
    @pytest.fixture
    def generate_planner(self, sample_config):
        """Provide a GeneratePlanner instance for testing."""
        return GeneratePlanner(sample_config)
    
    def test_initialization(self, sample_config):
        """Test GeneratePlanner initialization."""
        planner = GeneratePlanner(sample_config)
        assert planner.config == sample_config
    
    def test_generate_complete_output(self, generate_planner, sample_schedule):
        """Test complete output generation."""
        output = generate_planner.generate_complete_output(sample_schedule)
        
        assert isinstance(output, CompleteOutput)
        assert output.schedule == sample_schedule
        assert output.summary_metrics is not None
        assert output.detailed_metrics is not None
        assert output.schedule_table is not None
        assert output.metrics_table is not None
        assert output.deadline_table is not None
    
    def test_generate_complete_output_empty_schedule(self, generate_planner):
        """Test complete output generation with empty schedule."""
        empty_schedule = {}
        output = generate_planner.generate_complete_output(empty_schedule)
        
        assert isinstance(output, CompleteOutput)
        assert output.schedule == empty_schedule
        assert output.summary_metrics is not None
        assert output.detailed_metrics is not None
        assert output.schedule_table is not None
        assert output.metrics_table is not None
        assert output.deadline_table is not None
    
    @patch('src.output.generate_planner.create_output_directory')
    @patch('src.output.generate_planner.save_all_outputs')
    def test_save_output_to_files(self, mock_save_all, mock_create_dir, generate_planner, sample_schedule):
        """Test saving output to files."""
        mock_create_dir.return_value = "test_output_dir"
        mock_save_all.return_value = {
            "schedule.json": "test_output_dir/schedule.json",
            "metrics.csv": "test_output_dir/metrics.csv"
        }
        
        output = generate_planner.generate_complete_output(sample_schedule)
        saved_files = generate_planner.save_output_to_files(output, "test_output")
        
        assert isinstance(saved_files, dict)
        assert "schedule.json" in saved_files
        assert "metrics.csv" in saved_files
        mock_create_dir.assert_called_once_with("test_output")
        mock_save_all.assert_called_once()
    
    @patch('builtins.print')
    def test_print_output_summary(self, mock_print, generate_planner, sample_schedule):
        """Test printing output summary."""
        output = generate_planner.generate_complete_output(sample_schedule)
        generate_planner.print_output_summary(output)
        
        # Verify that print was called multiple times (for the summary)
        assert mock_print.call_count > 0
        
        # Check that the summary sections are printed
        printed_text = "".join([call.args[0] for call in mock_print.call_args_list])
        assert "SCHEDULE SUMMARY" in printed_text
        assert "QUALITY METRICS" in printed_text
        assert "COMPLIANCE METRICS" in printed_text
    
    @patch('src.output.generate_planner.generate_complete_output')
    @patch('src.output.generate_planner.save_output_to_files')
    @patch('src.output.generate_planner.print_output_summary')
    @patch('src.output.generate_planner.get_output_summary')
    @patch('builtins.print')
    def test_generate_and_save_output(self, mock_print, mock_get_summary, mock_print_summary, 
                                     mock_save_files, mock_generate_output, generate_planner, sample_schedule):
        """Test the complete generate and save workflow."""
        mock_output = MagicMock()
        mock_generate_output.return_value = mock_output
        mock_save_files.return_value = {"test.json": "test_path"}
        mock_get_summary.return_value = "Files saved successfully"
        
        result = generate_planner.generate_and_save_output(sample_schedule, "test_output")
        
        assert result == mock_output
        mock_generate_output.assert_called_once_with(sample_schedule)
        mock_print_summary.assert_called_once_with(mock_output)
        mock_save_files.assert_called_once_with(mock_output, "test_output")
        mock_get_summary.assert_called_once_with({"test.json": "test_path"})
        
        # Verify print was called for the file summary
        assert mock_print.call_count > 0
    
    def test_generate_and_save_output_default_dir(self, generate_planner, sample_schedule):
        """Test generate and save with default output directory."""
        with patch.object(generate_planner, 'generate_complete_output') as mock_generate:
            mock_output = MagicMock()
            mock_generate.return_value = mock_output
            
            with patch.object(generate_planner, 'save_output_to_files') as mock_save:
                mock_save.return_value = {}
                
                with patch.object(generate_planner, 'print_output_summary'):
                    with patch('src.output.generate_planner.get_output_summary'):
                        result = generate_planner.generate_and_save_output(sample_schedule)
                        
                        assert result == mock_output
                        mock_save.assert_called_once_with(mock_output, "output")
    
    def test_output_with_multiple_submissions(self, generate_planner):
        """Test output generation with multiple submissions."""
        multi_schedule = {
            "J1-pap": date(2024, 11, 1),
            "J2-pap": date(2024, 12, 1),
            "J3-pap": date(2025, 1, 1)
        }
        
        output = generate_planner.generate_complete_output(multi_schedule)
        
        assert output.schedule == multi_schedule
        assert len(output.schedule_table) > 0
        assert output.summary_metrics.total_submissions >= 0
        assert output.detailed_metrics is not None
    
    def test_validate_schedule(self, generate_planner, sample_schedule):
        """Test schedule validation."""
        # Valid schedule
        assert generate_planner.validate_schedule(sample_schedule) is True
        
        # Empty schedule
        assert generate_planner.validate_schedule({}) is False
        
        # Incomplete schedule
        incomplete_schedule = {"J1-pap": date(2024, 11, 1)}
        # Add another submission to config but not to schedule
        extra_submission = Submission(
            id="J2-pap",
            title="Extra Paper",
            kind=SubmissionType.PAPER,
            conference_id="ICML",
            depends_on=[],
            draft_window_months=2,
            lead_time_from_parents=0,
            penalty_cost_per_day=400,
            engineering=True,
            earliest_start_date=date(2024, 11, 1)
        )
        generate_planner.config.submissions.append(extra_submission)
        
        assert generate_planner.validate_schedule(incomplete_schedule) is False
    
    def test_get_schedule_statistics(self, generate_planner, sample_schedule):
        """Test getting schedule statistics."""
        stats = generate_planner.get_schedule_statistics(sample_schedule)
        
        assert isinstance(stats, dict)
        assert "total_submissions" in stats
        assert "scheduled_submissions" in stats
        assert "completion_rate" in stats
        assert "schedule_span_days" in stats
        assert "avg_daily_load" in stats
        assert "peak_daily_load" in stats
        
        assert stats["total_submissions"] == 1
        assert stats["scheduled_submissions"] == 1
        assert stats["completion_rate"] == 100.0
    
    def test_get_schedule_statistics_empty(self, generate_planner):
        """Test getting schedule statistics for empty schedule."""
        stats = generate_planner.get_schedule_statistics({})
        
        assert isinstance(stats, dict)
        assert stats["total_submissions"] == 1  # From config
        assert stats["scheduled_submissions"] == 0
        assert stats["completion_rate"] == 0.0
        assert stats["schedule_span_days"] == 0
        assert stats["avg_daily_load"] == 0.0
        assert stats["peak_daily_load"] == 0
    
    def test_get_schedule_statistics_multiple_submissions(self, generate_planner):
        """Test getting schedule statistics for multiple submissions."""
        # Add more submissions to config
        extra_submission1 = Submission(
            id="J2-pap",
            title="Extra Paper 1",
            kind=SubmissionType.PAPER,
            conference_id="ICML",
            depends_on=[],
            draft_window_months=2,
            lead_time_from_parents=0,
            penalty_cost_per_day=400,
            engineering=True,
            earliest_start_date=date(2024, 11, 1)
        )
        extra_submission2 = Submission(
            id="J3-pap",
            title="Extra Paper 2",
            kind=SubmissionType.PAPER,
            conference_id="ICML",
            depends_on=[],
            draft_window_months=3,
            lead_time_from_parents=0,
            penalty_cost_per_day=300,
            engineering=True,
            earliest_start_date=date(2024, 12, 1)
        )
        generate_planner.config.submissions.extend([extra_submission1, extra_submission2])
        
        multi_schedule = {
            "J1-pap": date(2024, 11, 1),
            "J2-pap": date(2024, 12, 1),
            "J3-pap": date(2025, 1, 1)
        }
        
        stats = generate_planner.get_schedule_statistics(multi_schedule)
        
        assert stats["total_submissions"] == 3
        assert stats["scheduled_submissions"] == 3
        assert stats["completion_rate"] == 100.0
        assert stats["schedule_span_days"] > 0  # Should have some span
    
    def test_output_error_handling(self, generate_planner):
        """Test output generation error handling."""
        # Test with invalid schedule data
        invalid_schedule = {"invalid-id": "not-a-date"}
        
        with pytest.raises(Exception):
            generate_planner.generate_complete_output(invalid_schedule)
    
    def test_save_output_error_handling(self, generate_planner, sample_schedule):
        """Test save output error handling."""
        output = generate_planner.generate_complete_output(sample_schedule)
        
        with patch('src.output.generate_planner.create_output_directory') as mock_create:
            mock_create.side_effect = Exception("Directory creation failed")
            
            with pytest.raises(Exception):
                generate_planner.save_output_to_files(output, "invalid/path")
    
    def test_print_summary_with_empty_output(self, generate_planner):
        """Test printing summary with empty output."""
        empty_schedule = {}
        output = generate_planner.generate_complete_output(empty_schedule)
        
        with patch('builtins.print') as mock_print:
            generate_planner.print_output_summary(output)
            
            # Should still print something even with empty output
            assert mock_print.call_count > 0
