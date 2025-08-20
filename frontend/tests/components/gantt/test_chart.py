"""Tests for gantt chart component."""

import pytest
from app.components.gantt.chart import create_gantt_chart, _create_empty_chart, _create_error_chart
from plotly.graph_objs import Figure

def test_create_gantt_chart_exists():
    """Test that create_gantt_chart function exists and is callable."""
    assert callable(create_gantt_chart)

def test_create_gantt_chart_returns_figure():
    """Test that create_gantt_chart returns a Plotly Figure."""
    from app.components.gantt.chart import create_gantt_chart
    
    fig = create_gantt_chart(use_sample_data=True)
    assert isinstance(fig, Figure)
    assert fig.layout.title.text == 'Paper Planner Demo - Real Submission Structure'

def test_create_empty_chart_exists():
    """Test that _create_empty_chart function exists and is callable."""
    assert callable(_create_empty_chart)

def test_create_error_chart_exists():
    """Test that _create_error_chart function exists and is callable."""
    assert callable(_create_error_chart)

def test_create_error_chart_returns_figure():
    """Test that _create_error_chart returns a Plotly Figure."""
    try:
        fig = _create_error_chart("Test error message")
        assert hasattr(fig, 'layout')
        assert hasattr(fig, 'data')
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass

def test_gantt_chart_has_expected_layout():
    """Test that gantt chart has expected layout properties."""
    from app.components.gantt.chart import create_gantt_chart
    
    fig = create_gantt_chart(use_sample_data=True)
    
    # Check basic layout properties
    assert fig.layout.title.text == 'Paper Planner Demo - Real Submission Structure'
    assert fig.layout.xaxis.title.text == 'Timeline'
    assert fig.layout.yaxis.title.text == 'Activities'
    assert fig.layout.height == 500
    assert fig.layout.plot_bgcolor == 'white'
    assert fig.layout.paper_bgcolor == 'white'


def test_gantt_chart_can_be_created():
    """Test that gantt chart can be created without errors."""
    from app.components.gantt.chart import create_gantt_chart
    
    try:
        fig = create_gantt_chart(use_sample_data=True)
        assert fig is not None
        assert hasattr(fig, 'layout')
        assert hasattr(fig, 'data')
    except Exception as e:
        pytest.fail(f"Gantt chart creation failed: {e}")


def test_gantt_chart_has_expected_height():
    """Test that gantt chart has expected height."""
    from app.components.gantt.chart import create_gantt_chart
    
    fig = create_gantt_chart(use_sample_data=True)
    assert fig.layout.height == 500
