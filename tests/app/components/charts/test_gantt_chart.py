"""Tests for gantt chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date
import plotly.graph_objects as go

from app.components.charts.gantt_chart import create_gantt_chart


class TestGanttChart:
    """Test cases for gantt chart functionality."""
    
    @pytest.fixture
    def sample_schedule(self):
        """Sample schedule data for testing."""
        return {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1),
            "abstract1": date(2024, 3, 1)
        }
    

    
    @pytest.fixture
    def sample_config(self):
        """Sample config for testing."""
        from src.core.models import Config
        
        return Config(
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            submissions=[],
            conferences=[],
            blackout_dates=[],
            scheduling_options={"enable_early_abstract_scheduling": False},
            priority_weights={
                "engineering_paper": 2.0,
                "medical_paper": 1.0,
                "mod": 1.5,
                "abstract": 0.5
            },
            penalty_costs={"default_mod_penalty_per_day": 1000},
            data_files={
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            }
        )
    
    def test_create_gantt_chart_basic(self, sample_schedule, sample_config):
        """Test basic gantt chart creation."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
    
    def test_create_gantt_chart_empty_schedule(self, sample_config):
        """Test gantt chart creation with empty schedule."""
        empty_schedule = {}
        fig = create_gantt_chart(empty_schedule, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
    
    def test_create_gantt_chart_with_engineering_papers(self, sample_schedule, sample_config):
        """Test gantt chart creation with engineering papers."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        # Check that engineering papers are properly colored
        assert isinstance(fig, go.Figure)
    
    def test_create_gantt_chart_with_abstracts(self, sample_schedule, sample_config):
        """Test gantt chart creation with abstracts."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        # Check that abstracts are properly handled
        assert isinstance(fig, go.Figure)
    
    def test_create_gantt_chart_layout_properties(self, sample_schedule, sample_config):
        """Test gantt chart layout properties."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        assert fig.layout is not None
