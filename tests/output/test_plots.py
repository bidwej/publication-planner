"""Tests for the plots module."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import matplotlib.pyplot as plt

from core.models import Paper, Schedule, ScheduleItem, Config
from output.plots import plot_schedule, plot_utilization_chart, plot_deadline_compliance, _get_priority_color, _get_label


class TestPlotSchedule:
    """Test the plot_schedule function."""

    def test_plot_schedule_empty_schedule(self):
        """Test plotting empty schedule."""
        schedule = Mock(spec=Schedule)
        schedule.items = []
        schedule.start_date = date(2024, 1, 1)
        schedule.end_date = date(2024, 12, 31)
        
        config = Mock(spec=Config)
        config.submissions = []
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_schedule(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None

    def test_plot_schedule_with_papers(self):
        """Test plotting schedule with papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        
        paper2 = Mock(spec=Paper)
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        
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
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_schedule(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None

    def test_plot_schedule_with_save_path(self):
        """Test plotting schedule with custom save path."""
        schedule = Mock(spec=Schedule)
        schedule.items = []
        schedule.start_date = date(2024, 1, 1)
        schedule.end_date = date(2024, 12, 31)
        
        config = Mock(spec=Config)
        config.submissions = []
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_schedule(schedule, config, save_path="/test/schedule.png")
            
            mock_savefig.assert_called_once_with("/test/schedule.png", dpi=300, bbox_inches='tight')


class TestPlotUtilizationChart:
    """Test the plot_utilization_chart function."""

    def test_plot_utilization_chart_empty_schedule(self):
        """Test plotting utilization chart with empty schedule."""
        schedule = Mock(spec=Schedule)
        schedule.items = []
        schedule.start_date = date(2024, 1, 1)
        schedule.end_date = date(2024, 12, 31)
        
        config = Mock(spec=Config)
        config.submissions = []
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_utilization_chart(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None

    def test_plot_utilization_chart_with_papers(self):
        """Test plotting utilization chart with papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        
        paper2 = Mock(spec=Paper)
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        
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
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_utilization_chart(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None


class TestPlotDeadlineCompliance:
    """Test the plot_deadline_compliance function."""

    def test_plot_deadline_compliance_empty_schedule(self):
        """Test plotting deadline compliance with empty schedule."""
        schedule = Mock(spec=Schedule)
        schedule.items = []
        schedule.start_date = date(2024, 1, 1)
        schedule.end_date = date(2024, 12, 31)
        
        config = Mock(spec=Config)
        config.submissions = []
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_deadline_compliance(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None

    def test_plot_deadline_compliance_with_papers(self):
        """Test plotting deadline compliance with papers."""
        # Create mock papers
        paper1 = Mock(spec=Paper)
        paper1.title = "Test Paper 1"
        paper1.deadline = date(2024, 6, 1)
        paper1.estimated_hours = 40
        
        paper2 = Mock(spec=Paper)
        paper2.title = "Test Paper 2"
        paper2.deadline = date(2024, 8, 1)
        paper2.estimated_hours = 60
        
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
        
        with patch('output.plots.plt.subplots') as mock_subplots, \
             patch('output.plots.plt.savefig') as mock_savefig:
            
            mock_fig, mock_ax = Mock(), Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            result = plot_deadline_compliance(schedule, config)
            
            mock_subplots.assert_called_once()
            mock_savefig.assert_called_once()
            assert result is not None


class TestGetPriorityColor:
    """Test the _get_priority_color function."""

    def test_get_priority_color_high(self):
        """Test getting color for high priority."""
        result = _get_priority_color("high")
        assert result == "red"

    def test_get_priority_color_medium(self):
        """Test getting color for medium priority."""
        result = _get_priority_color("medium")
        assert result == "orange"

    def test_get_priority_color_low(self):
        """Test getting color for low priority."""
        result = _get_priority_color("low")
        assert result == "green"

    def test_get_priority_color_unknown(self):
        """Test getting color for unknown priority."""
        result = _get_priority_color("unknown")
        assert result == "gray"


class TestGetLabel:
    """Test the _get_label function."""

    def test_get_label_short_title(self):
        """Test getting label for short title."""
        result = _get_label("Short Title", max_length=20)
        assert result == "Short Title"

    def test_get_label_long_title(self):
        """Test getting label for long title."""
        long_title = "This is a very long title that should be truncated"
        result = _get_label(long_title, max_length=20)
        assert len(result) <= 20
        assert result.endswith("...")

    def test_get_label_exact_length(self):
        """Test getting label for title at exact max length."""
        title = "Exactly 20 chars"
        result = _get_label(title, max_length=20)
        assert result == title

    def test_get_label_empty_title(self):
        """Test getting label for empty title."""
        result = _get_label("", max_length=20)
        assert result == ""
