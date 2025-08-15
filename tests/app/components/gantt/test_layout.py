"""Tests for gantt layout component."""
from datetime import date
import plotly.graph_objects as go

from unittest.mock import Mock, patch
from plotly.graph_objs import Figure, Layout

from app.components.gantt.layout import configure_gantt_layout
from app.components.gantt.timeline import get_title_text


class TestGanttLayout:
    """Test cases for gantt layout functionality."""
    
    # Use fixtures from conftest.py instead of defining them here
    
    def test_configure_gantt_layout_success(self, sample_timeline_range):
        """Test successful layout configuration."""
        fig: Figure = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        # Check that layout was updated
        assert fig.layout is not None
        # Access layout attributes directly - they exist at runtime
        assert hasattr(fig.layout, 'title')
        assert hasattr(fig.layout, 'xaxis')
        assert hasattr(fig.layout, 'yaxis')
    
    def test_configure_gantt_layout_title(self, sample_timeline_range):
        """Test that title is configured correctly."""
        fig: Figure = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        title = fig.layout.title
        assert title is not None
        assert title.text is not None
        assert "Paper Submission Timeline" in title.text
        assert title.x == 0.5
        assert title.xanchor == 'center'
        # Access font attributes safely
        font = getattr(title, 'font', None)
        if font:
            assert font.size == 18
            assert font.color == '#2c3e50'
    
    def test_configure_gantt_layout_height_calculation(self, sample_timeline_range):
        """Test that height is calculated correctly based on concurrency."""
        fig: Figure = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        # Height should be 400 + (max_concurrency * 30)
        # sample_timeline_range has max_concurrency = 4
        expected_height = 400 + (4 * 30)  # 400 + 120 = 520
        layout = fig.layout
        assert layout.height == expected_height
    
    def test_configure_gantt_layout_margins(self, sample_timeline_range):
        """Test that margins are set correctly."""
        fig: Figure = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        layout = fig.layout
        margins = layout.margin
        assert margins.l == 80  # left margin
        assert margins.r == 80  # right margin
        assert margins.t == 100  # top margin
        assert margins.b == 80   # bottom margin
    
    def test_configure_gantt_layout_background_colors(self, sample_timeline_range):
        """Test that background colors are set correctly."""
        fig = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        assert fig.layout.plot_bgcolor == 'white'
        assert fig.layout.paper_bgcolor == 'white'
    
    def test_configure_gantt_layout_xaxis(self, sample_timeline_range):
        """Test that x-axis is configured correctly."""
        fig = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        xaxis = fig.layout.xaxis
        assert xaxis.type == 'date'
        # Plotly returns tuples for ranges, so convert to list for comparison
        expected_range = [sample_timeline_range['min_date'], sample_timeline_range['max_date']]
        assert list(xaxis.range) == expected_range
        assert xaxis.title.text == 'Timeline'
        assert xaxis.showgrid is True
        assert xaxis.gridcolor == '#ecf0f1'
    
    def test_configure_gantt_layout_yaxis(self, sample_timeline_range):
        """Test that y-axis is configured correctly."""
        fig = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        yaxis = fig.layout.yaxis
        assert yaxis.title.text == 'Activities'
        expected_range = [-0.5, sample_timeline_range['max_concurrency'] + 0.5]
        assert list(yaxis.range) == expected_range
        assert yaxis.tickmode == 'linear'
        assert yaxis.dtick == 1
        assert yaxis.showgrid is True
        assert yaxis.gridcolor == '#ecf0f1'
    
    def test_configure_gantt_layout_legend(self, sample_timeline_range):
        """Test that legend is configured correctly."""
        fig = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        assert fig.layout.showlegend is False
    
    def test_configure_gantt_layout_different_concurrency(self, sample_timeline_range):
        """Test layout configuration with different concurrency values."""
        fig = go.Figure()
        
        # Test with high concurrency
        high_concurrency_range = sample_timeline_range.copy()
        high_concurrency_range['max_concurrency'] = 10
        
        configure_gantt_layout(fig, high_concurrency_range)
        
        expected_height = 400 + (10 * 30)  # 400 + 300 = 700
        assert fig.layout.height == expected_height
        
        # Test y-axis range
        yaxis = fig.layout.yaxis
        expected_range = [-0.5, 10.5]
        assert list(yaxis.range) == expected_range
    
    def test_configure_gantt_layout_zero_concurrency(self, sample_timeline_range):
        """Test layout configuration with zero concurrency."""
        fig = go.Figure()
        
        zero_concurrency_range = sample_timeline_range.copy()
        zero_concurrency_range['max_concurrency'] = 0
        
        configure_gantt_layout(fig, zero_concurrency_range)
        
        expected_height = 400 + (0 * 30)  # 400 + 0 = 400
        assert fig.layout.height == expected_height
        
        # Test y-axis range
        yaxis = fig.layout.yaxis
        expected_range = [-0.5, 0.5]
        assert list(yaxis.range) == expected_range
    
    def test_configure_gantt_layout_date_range(self, sample_timeline_range):
        """Test that date range is properly set in x-axis."""
        fig = go.Figure()
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        xaxis = fig.layout.xaxis
        # Use the actual dates from the fixture instead of hardcoded dates
        expected_range = [sample_timeline_range['min_date'], sample_timeline_range['max_date']]
        assert list(xaxis.range) == expected_range
    
    def test_configure_gantt_layout_title_text_generation(self, sample_timeline_range):
        """Test that title text is generated using the timeline function."""
        fig = go.Figure()
        
        # Mock the get_title_text function to verify it's called
        with patch('app.components.gantt.layout.get_title_text') as mock_get_title:
            mock_get_title.return_value = "Mock Title"
            configure_gantt_layout(fig, sample_timeline_range)
            
            mock_get_title.assert_called_once_with(sample_timeline_range)
            assert fig.layout.title.text == "Mock Title"
    
    def test_configure_gantt_layout_figure_preservation(self, sample_timeline_range):
        """Test that existing figure properties are preserved."""
        fig = go.Figure()
        
        # Add some existing properties
        fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))
        fig.update_layout(showlegend=True)
        
        configure_gantt_layout(fig, sample_timeline_range)
        
        # Check that existing trace is preserved
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatter'
        
        # Check that showlegend is overridden to False
        assert fig.layout.showlegend is False
    
    def test_configure_gantt_layout_multiple_calls(self, sample_timeline_range):
        """Test that multiple layout configurations work correctly."""
        fig = go.Figure()
        
        # First configuration
        configure_gantt_layout(fig, sample_timeline_range)
        first_height = fig.layout.height
        
        # Second configuration with different concurrency
        second_range = sample_timeline_range.copy()
        second_range['max_concurrency'] = 5
        configure_gantt_layout(fig, second_range)
        
        # Height should be updated
        assert fig.layout.height != first_height
        assert fig.layout.height == 400 + (5 * 30)  # 400 + 150 = 550
    
    def test_configure_gantt_layout_edge_case_dates(self):
        """Test layout configuration with edge case dates."""
        fig = go.Figure()
        
        # Test with same date
        same_date_range = {
            'min_date': date(2024, 6, 15),
            'max_date': date(2024, 6, 15),
            'timeline_start': date(2024, 6, 15),
            'span_days': 0,
            'max_concurrency': 1
        }
        
        configure_gantt_layout(fig, same_date_range)
        
        xaxis = fig.layout.xaxis
        expected_range = [date(2024, 6, 15), date(2024, 6, 15)]
        assert list(xaxis.range) == expected_range
        assert fig.layout.height == 400 + (1 * 30)  # 430
    
    def test_configure_gantt_layout_very_high_concurrency(self):
        """Test layout configuration with very high concurrency."""
        fig = go.Figure()
        
        very_high_range = {
            'min_date': date(2024, 4, 1),
            'max_date': date(2024, 8, 1),
            'timeline_start': date(2024, 4, 1),
            'span_days': 120,
            'max_concurrency': 100
        }
        
        configure_gantt_layout(fig, very_high_range)
        
        expected_height = 400 + (100 * 30)  # 400 + 3000 = 3400
        assert fig.layout.height == expected_height
        
        yaxis = fig.layout.yaxis
        expected_range = [-0.5, 100.5]
        assert list(yaxis.range) == expected_range
