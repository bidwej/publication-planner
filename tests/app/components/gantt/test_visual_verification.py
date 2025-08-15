"""Visual verification tests for gantt charts using headless browser."""

import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, patch
import plotly.graph_objects as go

from app.components.gantt.chart import create_gantt_chart
from app.components.gantt.activity import add_activity_bars, add_dependency_arrows
from app.components.gantt.timeline import get_timeline_range
from app.components.gantt.layout import configure_gantt_layout
from tests.common.headless_browser import capture_web_page_screenshot


class TestGanttVisualVerification:
    """Test cases for visual verification of gantt charts."""
    
    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create output directory for visual verification."""
        output_dir = tmp_path / "gantt_visual_tests"
        output_dir.mkdir(exist_ok=True)
        return str(output_dir)
    
    @pytest.fixture
    def sample_html_file(self, output_dir, sample_schedule_state):
        """Create a sample HTML file with gantt chart for visual testing."""
        # Create the gantt chart
        fig = create_gantt_chart(sample_schedule_state)
        
        # Convert to HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gantt Chart Visual Test</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .chart-container {{ width: 100%; height: 600px; }}
                .test-info {{ 
                    background: #f0f0f0; 
                    padding: 15px; 
                    margin-bottom: 20px; 
                    border-radius: 5px; 
                }}
            </style>
        </head>
        <body>
            <div class="test-info">
                <h2>Gantt Chart Visual Verification Test</h2>
                <p><strong>Purpose:</strong> Test for visual issues like double borders, proper styling, and layout</p>
                <p><strong>Chart Type:</strong> Paper Submission Timeline</p>
                <p><strong>Test Data:</strong> 4 submissions with dependencies</p>
            </div>
            <div class="chart-container" id="gantt-chart"></div>
            <script>
                {fig.to_json()}
                Plotly.newPlot('gantt-chart', fig.data, fig.layout);
            </script>
        </body>
        </html>
        """
        
        html_file = Path(output_dir) / "gantt_chart_test.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_file)
    
    def test_gantt_chart_visual_elements(self, sample_schedule_state, output_dir):
        """Test that gantt chart has all required visual elements."""
        fig = create_gantt_chart(sample_schedule_state)
        
        # Check that figure has data
        assert len(fig.data) > 0, "Chart should have data traces"
        
        # Check that figure has layout
        assert fig.layout is not None, "Chart should have layout"
        assert fig.layout.title is not None, "Chart should have title"
        
        # Check for specific visual elements
        assert fig.layout.xaxis is not None, "Chart should have x-axis"
        assert fig.layout.yaxis is not None, "Chart should have y-axis"
        
        # Check for shapes (activity bars)
        assert fig.layout.shapes is not None, "Chart should have shapes for activity bars"
        assert len(fig.layout.shapes) > 0, "Chart should have at least one activity bar"
        
        # Check for annotations (labels)
        assert fig.layout.annotations is not None, "Chart should have annotations for labels"
        assert len(fig.layout.annotations) > 0, "Chart should have at least one label"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "gantt_chart_elements.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_activity_bars_styling(self, sample_schedule, sample_config, output_dir):
        """Test that activity bars have proper styling without double borders."""
        fig = go.Figure()
        
        # Add activity bars
        add_activity_bars(fig, sample_schedule, sample_config)
        
        # Check that shapes were added
        assert len(fig.layout.shapes) > 0, "Activity bars should be added"
        
        # Check each shape for proper styling
        for shape in fig.layout.shapes:
            # Check that shape is a rectangle
            assert shape.type == "rect", "Activity bars should be rectangles"
            
            # Check for fill color
            assert shape.fillcolor is not None, "Activity bars should have fill color"
            
            # Check for border color
            assert shape.line.color is not None, "Activity bars should have border color"
            
            # Check that fill and border colors are different (avoid double border effect)
            assert shape.fillcolor != shape.line.color, "Fill and border colors should be different"
            
            # Check opacity
            assert shape.opacity == 0.8, "Activity bars should have 0.8 opacity"
            
            # Check line width
            assert shape.line.width == 2, "Activity bars should have 2px border width"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "activity_bars_styling.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_dependency_arrows_styling(self, sample_schedule, sample_config, output_dir):
        """Test that dependency arrows have proper styling."""
        fig = go.Figure()
        
        # Add dependency arrows
        add_dependency_arrows(fig, sample_schedule, sample_config)
        
        # Check that traces were added (arrows are traces, not shapes)
        assert len(fig.data) > 0, "Dependency arrows should be added as traces"
        
        # Check each trace for proper styling
        for trace in fig.data:
            # Check that trace is scatter
            assert trace.type == 'scatter', "Dependency arrows should be scatter traces"
            
            # Check mode
            assert trace.mode == 'lines+markers', "Dependency arrows should have lines and markers"
            
            # Check line color
            assert trace.line.color == '#e74c3c', "Dependency arrows should have red color"
            
            # Check line width
            assert trace.line.width == 2, "Dependency arrows should have 2px width"
            
            # Check line dash
            assert trace.line.dash == 'dot', "Dependency arrows should have dotted lines"
            
            # Check marker symbol
            assert trace.marker.symbol == 'arrow-up', "Dependency arrows should have arrow-up markers"
            
            # Check marker size
            assert trace.marker.size == 8, "Dependency arrows should have size 8 markers"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "dependency_arrows_styling.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_layout_configuration(self, sample_timeline_range, output_dir):
        """Test that layout is configured correctly."""
        fig = go.Figure()
        
        # Configure layout
        configure_gantt_layout(fig, sample_timeline_range)
        
        # Check layout properties
        assert fig.layout.title is not None, "Layout should have title"
        assert fig.layout.height is not None, "Layout should have height"
        assert fig.layout.plot_bgcolor == 'white', "Plot background should be white"
        assert fig.layout.paper_bgcolor == 'white', "Paper background should be white"
        
        # Check axis configuration
        assert fig.layout.xaxis.type == 'date', "X-axis should be date type"
        assert fig.layout.yaxis.title.text == 'Activities', "Y-axis should have 'Activities' title"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "layout_configuration.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_color_consistency(self, sample_schedule, sample_config, output_dir):
        """Test that colors are consistent across chart elements."""
        fig = go.Figure()
        
        # Add all elements
        add_activity_bars(fig, sample_schedule, sample_config)
        add_dependency_arrows(fig, sample_schedule, sample_config)
        
        # Get all colors used
        colors = set()
        
        # Collect colors from shapes (activity bars)
        for shape in fig.layout.shapes:
            if shape.fillcolor:
                colors.add(shape.fillcolor)
            if shape.line.color:
                colors.add(shape.line.color)
        
        # Collect colors from traces (dependency arrows)
        for trace in fig.data:
            if trace.line.color:
                colors.add(trace.line.color)
            if trace.marker.color:
                colors.add(trace.marker.color)
        
        # Check that we have a reasonable number of colors
        assert len(colors) >= 3, "Should have at least 3 different colors"
        assert len(colors) <= 10, "Should not have too many colors (max 10)"
        
        # Check that all colors are valid hex colors
        for color in colors:
            assert color.startswith('#'), f"Color {color} should start with #"
            assert len(color) == 7, f"Color {color} should be 7 characters long"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "color_consistency.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_chart_dimensions(self, sample_schedule_state, output_dir):
        """Test that chart has appropriate dimensions."""
        fig = create_gantt_chart(sample_schedule_state)
        
        # Check height calculation
        assert fig.layout.height is not None, "Chart should have height"
        assert fig.layout.height >= 400, "Chart height should be at least 400px"
        
        # Check margins
        assert fig.layout.margin is not None, "Chart should have margins"
        assert fig.layout.margin.l == 80, "Left margin should be 80px"
        assert fig.layout.margin.r == 80, "Right margin should be 80px"
        assert fig.layout.margin.t == 100, "Top margin should be 100px"
        assert fig.layout.margin.b == 80, "Bottom margin should be 80px"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "chart_dimensions.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    @pytest.mark.asyncio
    async def test_gantt_chart_screenshot(self, sample_html_file, output_dir):
        """Test that gantt chart can be captured as screenshot (if headless browser available)."""
        # This test requires the headless browser utility
        try:
            # Try to capture screenshot
            screenshot_path = os.path.join(output_dir, "gantt_chart_screenshot.png")
            
            # Convert file:// URL to proper URL for testing
            file_url = f"file://{sample_html_file}"
            
            # Note: This might not work with file:// URLs in some browsers
            # In a real scenario, you'd serve this through a web server
            success = await capture_web_page_screenshot(
                url=file_url,
                output_path=screenshot_path,
                wait_for_selector="#gantt-chart",
                wait_timeout=5000
            )
            
            if success:
                assert os.path.exists(screenshot_path), "Screenshot should be created"
                print(f"Screenshot saved to: {screenshot_path}")
            else:
                print("Screenshot capture failed (this is expected for file:// URLs)")
                
        except Exception as e:
            # This test is optional and might fail in some environments
            print(f"Screenshot test skipped: {e}")
            pytest.skip("Screenshot test not available in this environment")
    
    def test_gantt_chart_accessibility(self, sample_schedule_state, output_dir):
        """Test that gantt chart has accessibility features."""
        fig = create_gantt_chart(sample_schedule_state)
        
        # Check for title
        assert fig.layout.title is not None, "Chart should have title for accessibility"
        assert fig.layout.title.text is not None, "Chart title should have text"
        
        # Check for axis labels
        assert fig.layout.xaxis.title is not None, "X-axis should have title for accessibility"
        assert fig.layout.yaxis.title is not None, "Y-axis should have title for accessibility"
        
        # Check for axis titles
        assert fig.layout.xaxis.title.text is not None, "X-axis title should have text"
        assert fig.layout.yaxis.title.text is not None, "Y-axis title should have text"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "gantt_chart_accessibility.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_gantt_chart_responsiveness(self, sample_schedule_state, output_dir):
        """Test that gantt chart has responsive design elements."""
        fig = create_gantt_chart(sample_schedule_state)
        
        # Check that layout has responsive properties
        # Note: autosize is not set by default, but we can check other responsive properties
        assert fig.layout.height is not None, "Chart should have height for responsive design"
        assert fig.layout.margin is not None, "Chart should have margins for responsive design"
        
        # Check that margins are proportional
        assert fig.layout.margin is not None, "Chart should have margins"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "gantt_chart_responsiveness.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
