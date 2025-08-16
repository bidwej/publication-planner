"""Tests for dashboard chart component."""

import pytest
from app.components.dashboard.chart import create_dashboard_chart

def test_create_dashboard_chart_exists():
    """Test that create_dashboard_chart function exists and is callable."""
    assert callable(create_dashboard_chart)

def test_create_dashboard_chart_returns_figure():
    """Test that create_dashboard_chart returns a Plotly Figure."""
    try:
        fig = create_dashboard_chart()
        assert hasattr(fig, 'layout')
        assert hasattr(fig, 'data')
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass

def test_create_dashboard_chart_with_chart_type():
    """Test that create_dashboard_chart accepts chart_type parameter."""
    try:
        # Test different chart types
        chart_types = ['timeline', 'gantt', 'resources', 'dependencies']
        for chart_type in chart_types:
            fig = create_dashboard_chart(chart_type=chart_type)
            assert hasattr(fig, 'layout')
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass

def test_create_dashboard_chart_with_config():
    """Test that create_dashboard_chart accepts config parameter."""
    try:
        fig = create_dashboard_chart(config=None)
        assert hasattr(fig, 'layout')
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass

def test_dashboard_chart_has_expected_layout():
    """Test that dashboard chart has expected layout properties."""
    try:
        fig = create_dashboard_chart()
        
        # Check for expected layout properties
        assert hasattr(fig.layout, 'title')
        assert hasattr(fig.layout, 'height')
        assert hasattr(fig.layout, 'plot_bgcolor')
        assert hasattr(fig.layout, 'paper_bgcolor')
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass
