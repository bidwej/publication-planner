"""Tests for gantt activity component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import plotly.graph_objects as go

from app.components.gantt.activity import (
    add_activity_bars, add_dependency_arrows,
    _add_bar_label, _add_dependency_arrow, _get_submission_color,
    _get_border_color, _get_display_title
)
from src.core.models import Config, Submission, SubmissionType


class TestGanttActivity:
    """Test cases for gantt activity functionality."""
    
    def test_add_activity_bars_success(self, sample_schedule, sample_config):
        """Test successful activity bar addition."""
        fig = go.Figure()
        
        add_activity_bars(fig, sample_schedule, sample_config)
        
        # Check that shapes were added (one for each submission)
        assert len(fig.layout.shapes) == len(sample_schedule)
        
        # Check that annotations were added (3 per submission: type, author, title)
        expected_annotations = len(sample_schedule) * 3
        assert len(fig.layout.annotations) == expected_annotations
    
    def test_add_activity_bars_empty_schedule(self, sample_config):
        """Test activity bar addition with empty schedule."""
        fig = go.Figure()
        empty_schedule = {}
        
        add_activity_bars(fig, empty_schedule, sample_config)
        
        # No shapes or annotations should be added
        assert len(fig.layout.shapes) == 0
        assert len(fig.layout.annotations) == 0
    
    def test_get_submission_color(self):
        """Test submission color selection."""
        # Test engineering paper (MOD - pccp author)
        engineering_submission = Submission(
            id="test1", title="Test", kind=SubmissionType.PAPER, author="pccp"
        )
        color = _get_submission_color(engineering_submission)
        assert color == "#3498db"  # Blue for engineering paper (MOD)
        
        # Test medical paper (ED - ed author)
        medical_submission = Submission(
            id="test2", title="Test", kind=SubmissionType.PAPER, author="ed"
        )
        color = _get_submission_color(medical_submission)
        assert color == "#9b59b6"  # Purple for medical paper (ED)
        
        # Test abstract
        abstract_submission = Submission(
            id="test3", title="Test", kind=SubmissionType.ABSTRACT, author="pccp"
        )
        color = _get_submission_color(abstract_submission)
        assert color == "#85c1e9"  # Light blue for engineering abstract
    
    def test_get_border_color(self):
        """Test border color selection."""
        # Test engineering paper (MOD - pccp author)
        engineering_submission = Submission(
            id="test1", title="Test", kind=SubmissionType.PAPER, author="pccp"
        )
        border_color = _get_border_color(engineering_submission)
        assert border_color == "#2980b9"  # Darker blue for engineering paper (MOD)
        
        # Test medical paper (ED - ed author)
        medical_submission = Submission(
            id="test2", title="Test", kind=SubmissionType.PAPER, author="ed"
        )
        border_color = _get_border_color(medical_submission)
        assert border_color == "#8e44ad"  # Darker purple for medical paper (ED)
        
        # Test abstract
        abstract_submission = Submission(
            id="test3", title="Test", kind=SubmissionType.ABSTRACT, author="pccp"
        )
        border_color = _get_border_color(abstract_submission)
        assert border_color == "#5dade2"  # Medium blue for engineering abstract border
    
    def test_get_display_title(self):
        """Test display title generation."""
        # Test long title truncation
        long_title = "This is a very long title that should be truncated to fit in the gantt chart"
        submission = Submission(
            id="test1", title=long_title, kind=SubmissionType.PAPER, author="pccp"
        )
        display_title = _get_display_title(submission)
        assert len(display_title) <= 28  # Should be truncated to 25 + "..."
        
        # Test short title (no truncation needed)
        short_title = "Short Title"
        submission = Submission(
            id="test2", title=short_title, kind=SubmissionType.PAPER, author="pccp"
        )
        display_title = _get_display_title(submission)
        assert display_title == short_title
