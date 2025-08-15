"""Tests for metrics chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import plotly.graph_objects as go

from app.components.metrics_chart import (
    create_metrics_chart, create_score_comparison_chart, 
    create_timeline_metrics_chart, _calculate_timeline_metrics,
    _create_empty_metrics
)
from src.core.models import Config
from typing import Dict, List, Any, Optional


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
    
    @pytest.fixture
    def sample_schedule(self):
        """Sample schedule data for testing."""
        return {
            "paper1": date(2024, 5, 1),
            "paper2": date(2024, 7, 1),
            "paper3": date(2024, 6, 15)
        }
    
    @pytest.fixture
    def sample_scores_data(self):
        """Sample scores data for comparison chart."""
        return [
            {
                "strategy": "greedy",
                "penalty_score": 15.0,
                "quality_score": 85.0,
                "efficiency_score": 80.0
            },
            {
                "strategy": "optimal",
                "penalty_score": 10.0,
                "quality_score": 90.0,
                "efficiency_score": 85.0
            },
            {
                "strategy": "stochastic",
                "penalty_score": 18.0,
                "quality_score": 82.0,
                "efficiency_score": 78.0
            }
        ]
    
    def test_create_metrics_chart_basic(self, sample_validation_result, sample_config):
        """Test basic metrics chart creation."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title is not None
        assert "Performance Metrics" in fig.layout.title.text
    
    def test_create_metrics_chart_empty_result(self, sample_config):
        """Test metrics chart creation with empty validation result."""
        empty_result: Dict[str, Any] = {}
        fig = create_metrics_chart(empty_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_metrics_chart_none_result(self, sample_config):
        """Test metrics chart creation with None validation result."""
        fig = create_metrics_chart(None, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_metrics_chart_with_scores(self, sample_validation_result, sample_config):
        """Test metrics chart creation with scores."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        # Check that scores are properly displayed
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        
        # Check trace data
        trace = fig.data[0]
        assert trace.type == 'scatterpolar'
        assert trace.fill == 'toself'
        assert trace.name == 'Performance'
        assert trace.line.color == '#2E86AB'
    
    def test_create_metrics_chart_with_violations(self, sample_validation_result, sample_config):
        """Test metrics chart creation with violations."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        # Check that violations are properly displayed
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
    
    def test_create_metrics_chart_layout_properties(self, sample_validation_result, sample_config):
        """Test metrics chart layout properties."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        assert fig.layout is not None
        assert fig.layout.title.text == 'Performance Metrics'
        assert fig.layout.title.x == 0.5
        assert fig.layout.title.xanchor == 'center'
        assert fig.layout.height == 400
        assert fig.layout.showlegend is False
    
    def test_create_metrics_chart_polar_configuration(self, sample_validation_result, sample_config):
        """Test that polar chart is configured correctly."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        assert fig.layout.polar is not None
        assert fig.layout.polar.radialaxis.visible is True
        # Plotly returns tuples for ranges, so convert to list for comparison
        assert list(fig.layout.polar.radialaxis.range) == [0, 100]
    
    def test_create_metrics_chart_with_missing_data(self, sample_config):
        """Test metrics chart creation with missing data."""
        partial_result: Dict[str, Any] = {
            "overall_score": 85.5,
            "quality_score": 90.0
            # Missing other fields
        }
        fig = create_metrics_chart(partial_result, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_metrics_chart_with_no_scores(self, sample_config):
        """Test metrics chart creation with no scores."""
        result_without_scores: Dict[str, Any] = {
            "constraint_violations": {"deadline_violations": 2},
            "metrics": {"resource_utilization": 75.0}
        }
        fig = create_metrics_chart(result_without_scores, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_score_comparison_chart_success(self, sample_scores_data):
        """Test successful score comparison chart creation."""
        fig = create_score_comparison_chart(sample_scores_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'Strategy Comparison'
        assert fig.layout.height == 400
    
    def test_create_score_comparison_chart_empty_data(self):
        """Test score comparison chart creation with empty data."""
        empty_data: List[Dict[str, Any]] = []
        fig = create_score_comparison_chart(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_score_comparison_chart_none_data(self):
        """Test score comparison chart creation with None data."""
        fig = create_score_comparison_chart(None)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_score_comparison_chart_traces(self, sample_scores_data):
        """Test that comparison chart has correct traces."""
        fig = create_score_comparison_chart(sample_scores_data)
        
        assert len(fig.data) == 3
        
        # Check penalty trace
        penalty_trace = fig.data[0]
        assert penalty_trace.name == 'Penalty'
        assert penalty_trace.marker.color == '#A23B72'
        
        # Check quality trace
        quality_trace = fig.data[1]
        assert quality_trace.name == 'Quality'
        assert quality_trace.marker.color == '#F18F01'
        
        # Check efficiency trace
        efficiency_trace = fig.data[2]
        assert efficiency_trace.name == 'Efficiency'
        assert efficiency_trace.marker.color == '#C73E1D'
    
    def test_create_score_comparison_chart_data_values(self, sample_scores_data):
        """Test that comparison chart has correct data values."""
        fig = create_score_comparison_chart(sample_scores_data)
        
        # Check x-axis values (strategies) - Plotly returns tuples, convert to list
        expected_strategies = ['greedy', 'optimal', 'stochastic']
        assert list(fig.data[0].x) == expected_strategies
        
        # Check y-axis values for penalty scores - Plotly returns tuples, convert to list
        assert list(fig.data[0].y) == [15.0, 10.0, 18.0]
        
        # Check y-axis values for quality scores - Plotly returns tuples, convert to list
        assert list(fig.data[1].y) == [85.0, 90.0, 82.0]
        
        # Check y-axis values for efficiency scores - Plotly returns tuples, convert to list
        assert list(fig.data[2].y) == [80.0, 85.0, 78.0]
    
    def test_create_score_comparison_chart_layout(self, sample_scores_data):
        """Test comparison chart layout configuration."""
        fig = create_score_comparison_chart(sample_scores_data)
        
        layout = fig.layout
        assert layout.title.text == 'Strategy Comparison'
        assert layout.title.x == 0.5
        assert layout.title.xanchor == 'center'
        assert layout.xaxis.title.text == 'Strategy'
        assert layout.yaxis.title.text == 'Score'
        assert layout.barmode == 'group'
        assert layout.height == 400
    
    def test_create_timeline_metrics_chart_success(self, sample_schedule, sample_config):
        """Test successful timeline metrics chart creation."""
        fig = create_timeline_metrics_chart(sample_schedule, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'Timeline Workload'
        assert fig.layout.height == 400
    
    def test_create_timeline_metrics_chart_empty_schedule(self, sample_config):
        """Test timeline metrics chart creation with empty schedule."""
        empty_schedule: Dict[str, Any] = {}
        fig = create_timeline_metrics_chart(empty_schedule, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_timeline_metrics_chart_none_schedule(self, sample_config):
        """Test timeline metrics chart creation with None schedule."""
        fig = create_timeline_metrics_chart(None, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
    
    def test_create_timeline_metrics_chart_trace(self, sample_schedule, sample_config):
        """Test that timeline chart has correct trace."""
        fig = create_timeline_metrics_chart(sample_schedule, sample_config)
        
        assert len(fig.data) == 1
        
        trace = fig.data[0]
        assert trace.type == 'scatter'
        assert trace.mode == 'lines+markers'
        assert trace.name == 'Workload'
        assert trace.line.color == '#2E86AB'
        assert trace.line.width == 3
        assert trace.marker.size == 8
    
    def test_create_timeline_metrics_chart_layout(self, sample_schedule, sample_config):
        """Test timeline chart layout configuration."""
        fig = create_timeline_metrics_chart(sample_schedule, sample_config)
        
        layout = fig.layout
        assert layout.title.text == 'Timeline Workload'
        assert layout.title.x == 0.5
        assert layout.title.xanchor == 'center'
        assert layout.xaxis.title.text == 'Date'
        assert layout.yaxis.title.text == 'Active Submissions'
        assert layout.height == 400
        assert layout.showlegend is False
    
    def test_calculate_timeline_metrics_success(self, sample_schedule, sample_config):
        """Test successful timeline metrics calculation."""
        result = _calculate_timeline_metrics(sample_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert 'dates' in result
        assert 'workload' in result
        assert len(result['dates']) > 0
        assert len(result['workload']) > 0
        assert len(result['dates']) == len(result['workload'])
    
    def test_calculate_timeline_metrics_empty_schedule(self, sample_config):
        """Test timeline metrics calculation with empty schedule."""
        empty_schedule: Dict[str, Any] = {}
        result = _calculate_timeline_metrics(empty_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert result['dates'] == []
        assert result['workload'] == []
    
    def test_calculate_timeline_metrics_none_schedule(self, sample_config):
        """Test timeline metrics calculation with None schedule."""
        result = _calculate_timeline_metrics(None, sample_config)
        
        assert isinstance(result, dict)
        assert result['dates'] == []
        assert result['workload'] == []
    
    def test_calculate_timeline_metrics_date_range(self, sample_schedule, sample_config):
        """Test that timeline metrics cover correct date range."""
        result = _calculate_timeline_metrics(sample_schedule, sample_config)
        
        # Should start from earliest date in schedule
        earliest_date = min(sample_schedule.values())
        assert result['dates'][0] >= earliest_date
        
        # Should end at latest date + 90 days
        latest_date = max(sample_schedule.values())
        expected_end = latest_date + timedelta(days=90)
        assert result['dates'][-1] <= expected_end
    
    def test_calculate_timeline_metrics_weekly_intervals(self, sample_schedule, sample_config):
        """Test that timeline metrics use weekly intervals."""
        result = _calculate_timeline_metrics(sample_schedule, sample_config)
        
        if len(result['dates']) > 1:
            # Check that dates are approximately 7 days apart
            for i in range(1, len(result['dates'])):
                date_diff = (result['dates'][i] - result['dates'][i-1]).days
                assert 6 <= date_diff <= 8  # Allow for slight variations
    
    def test_calculate_timeline_metrics_workload_calculation(self, sample_schedule, sample_config):
        """Test that workload is calculated correctly."""
        result = _calculate_timeline_metrics(sample_schedule, sample_config)
        
        # Workload should be non-negative integers
        for workload in result['workload']:
            assert isinstance(workload, int)
            assert workload >= 0
    
    def test_create_empty_metrics(self):
        """Test empty metrics chart creation."""
        fig = _create_empty_metrics()
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Metrics Available'
        assert fig.layout.title.x == 0.5
        assert fig.layout.title.xanchor == 'center'
        assert fig.layout.height == 400
    
    def test_create_empty_metrics_annotation(self):
        """Test that empty metrics chart has proper annotation."""
        fig = _create_empty_metrics()
        
        annotations = fig.layout.annotations
        assert len(annotations) == 1
        
        annotation = annotations[0]
        assert annotation.text == 'Generate a schedule to see metrics'
        assert annotation.x == 0.5
        assert annotation.y == 0.5
        assert annotation.xref == 'paper'
        assert annotation.yref == 'paper'
        assert annotation.showarrow is False
        assert annotation.font.size == 16
        assert annotation.font.color == 'gray'
    
    def test_metrics_chart_colors(self, sample_validation_result, sample_config):
        """Test that metrics chart uses correct colors."""
        fig = create_metrics_chart(sample_validation_result, sample_config)
        
        trace = fig.data[0]
        assert trace.line.color == '#2E86AB'
    
    def test_comparison_chart_colors(self, sample_scores_data):
        """Test that comparison chart uses correct colors."""
        fig = create_score_comparison_chart(sample_scores_data)
        
        assert fig.data[0].marker.color == '#A23B72'  # Penalty
        assert fig.data[1].marker.color == '#F18F01'  # Quality
        assert fig.data[2].marker.color == '#C73E1D'  # Efficiency
    
    def test_timeline_chart_colors(self, sample_schedule, sample_config):
        """Test that timeline chart uses correct colors."""
        fig = create_timeline_metrics_chart(sample_schedule, sample_config)
        
        trace = fig.data[0]
        assert trace.line.color == '#2E86AB'
        assert trace.marker.size == 8
        assert trace.line.width == 3
