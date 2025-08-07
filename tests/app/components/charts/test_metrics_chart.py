"""Tests for metrics chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date
import plotly.graph_objects as go

from app.components.charts.metrics_chart import create_metrics_chart


class TestMetricsChart:
    """Test cases for metrics chart functionality."""
    
    @pytest.fixture
    def sample_validation_result(self):
        """Sample validation result for testing."""
        return {
            "scores": {
                "overall_score": 85.5,
                "quality_score": 90.0,
                "efficiency_score": 80.0,
                "penalty_score": 14.5
            },
            "constraint_violations": {
                "deadline_violations": 2,
                "dependency_violations": 0,
                "resource_violations": 1
            },
            "metrics": {
                "resource_utilization": 75.0,
                "timeline_efficiency": 85.0,
                "deadline_compliance": 90.0
            }
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
    
    def test_create_metrics_chart_basic(self, sample_validation_result, sample_config):
        """Test basic metrics chart creation."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
    
    def test_create_metrics_chart_empty_result(self, sample_config):
        """Test metrics chart creation with empty validation result."""
        empty_result = {}
        fig = create_metrics_chart(empty_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
    
    def test_create_metrics_chart_with_scores(self, sample_validation_result, sample_config):
        """Test metrics chart creation with scores."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        # Check that scores are properly displayed
        assert isinstance(fig, go.Figure)
    
    def test_create_metrics_chart_with_violations(self, sample_validation_result, sample_config):
        """Test metrics chart creation with violations."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        # Check that violations are properly displayed
        assert isinstance(fig, go.Figure)
    
    def test_create_metrics_chart_layout_properties(self, sample_validation_result, sample_config):
        """Test metrics chart layout properties."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        assert fig.layout is not None
    
    def test_create_metrics_chart_with_missing_data(self, sample_config):
        """Test metrics chart creation with missing data."""
        partial_result = {
            "overall_score": 85.5,
            "quality_score": 90.0
            # Missing other fields
        }
        fig = create_metrics_chart(partial_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
