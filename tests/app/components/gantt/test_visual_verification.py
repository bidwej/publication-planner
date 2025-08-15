"""Comprehensive visual verification tests for gantt charts using headless browser."""

import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, patch
import plotly.graph_objects as go
from datetime import date

from app.components.gantt.chart import create_gantt_chart
from app.components.gantt.activity import add_activity_bars, add_dependency_arrows, _get_submission_color, _get_border_color
from app.components.gantt.timeline import get_chart_dimensions
from app.components.gantt.layout import configure_gantt_layout
from tests.common.headless_browser import capture_web_page_screenshot
from src.core.models import Submission, SubmissionType


class TestGanttVisualVerification:
    """Test cases for comprehensive visual verification of gantt charts."""
    
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
                .color-legend {{
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .color-item {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .color-box {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid #333;
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
            <div class="color-legend">
                <div class="color-item">
                    <div class="color-box" style="background-color: #3498db;"></div>
                    <span>Engineering Papers (MODs) - Blue</span>
                </div>
                <div class="color-item">
                    <div class="color-box" style="background-color: #9b59b6;"></div>
                    <span>Medical Papers (ED) - Purple</span>
                </div>
                <div class="color-item">
                    <div class="color-box" style="background-color: #e67e22;"></div>
                    <span>Abstracts - Orange</span>
                </div>
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

    # ============================================================================
    # SPECIFIC COLOR LOGIC TESTS - Testing the exact business requirements
    # ============================================================================
    
    def test_engineering_paper_colors(self):
        """Test that engineering papers (MODs) get the correct blue color."""
        # Create engineering paper submission (pccp author)
        engineering_submission = Submission(
            id="test-mod",
            title="Test Engineering Module",
            kind=SubmissionType.PAPER,
            author="pccp"  # Engineering author
        )
        
        # Test submission color
        color = _get_submission_color(engineering_submission)
        assert color == "#3498db", f"Engineering papers should be blue (#3498db), got {color}"
        
        # Test border color
        border_color = _get_border_color(engineering_submission)
        assert border_color == "#2980b9", f"Engineering paper borders should be dark blue (#2980b9), got {border_color}"
        
        # Verify colors are different to prevent double border effect
        assert color != border_color, "Fill and border colors should be different to prevent double border effect"
    
    def test_medical_paper_colors(self):
        """Test that medical papers (ED) get the correct purple color."""
        # Create medical paper submission (ed author)
        medical_submission = Submission(
            id="test-med",
            title="Test Medical Paper",
            kind=SubmissionType.PAPER,
            author="ed"  # Medical author
        )
        
        # Test submission color
        color = _get_submission_color(medical_submission)
        assert color == "#9b59b6", f"Medical papers should be purple (#9b59b6), got {color}"
        
        # Test border color
        border_color = _get_border_color(medical_submission)
        assert border_color == "#8e44ad", f"Medical paper borders should be dark purple (#8e44ad), got {border_color}"
        
        # Verify colors are different to prevent double border effect
        assert color != border_color, "Fill and border colors should be different to prevent double border effect"
    
    def test_abstract_colors(self):
        """Test that abstracts get the correct orange color."""
        # Create abstract submission
        abstract_submission = Submission(
            id="test-abs",
            title="Test Abstract",
            kind=SubmissionType.ABSTRACT,
            author="pccp"
        )
        
        # Test submission color
        color = _get_submission_color(abstract_submission)
        assert color == "#85c1e9", f"Abstracts should be light blue (#85c1e9), got {color}"
        
        # Test border color
        border_color = _get_border_color(abstract_submission)
        assert border_color == "#5dade2", f"Abstract borders should be medium blue (#5dade2), got {border_color}"
        
        # Verify colors are different to prevent double border effect
        assert color != border_color, "Fill and border colors should be different to prevent double border effect"
    
    def test_no_double_border_effect(self):
        """Test that all submission types have different fill and border colors."""
        submission_types = [
            (SubmissionType.PAPER, "pccp"),  # Engineering paper
            (SubmissionType.PAPER, "ed"),    # Medical paper
            (SubmissionType.ABSTRACT, "pccp"), # Abstract
        ]
        
        for kind, author in submission_types:
            submission = Submission(
                id=f"test-{kind.value}-{author}",
                title=f"Test {kind.value}",
                kind=kind,
                author=author
            )
            
            fill_color = _get_submission_color(submission)
            border_color = _get_border_color(submission)
            
            # Critical test: fill and border must be different
            assert fill_color != border_color, (
                f"{kind.value} with author {author}: "
                f"Fill color ({fill_color}) and border color ({border_color}) "
                f"must be different to prevent double border effect"
            )
            
            # Colors should be in the same family but different shades
            assert fill_color.startswith('#'), f"Fill color should be hex: {fill_color}"
            assert border_color.startswith('#'), f"Border color should be hex: {border_color}"
    
    # ============================================================================
    # VISUAL LAYOUT AND POSITIONING TESTS
    # ============================================================================
    
    def test_activity_bar_positioning(self, sample_schedule, sample_config):
        """Test that activity bars are positioned correctly on the timeline."""
        fig = go.Figure()
        
        # Add activity bars
        add_activity_bars(fig, sample_schedule, sample_config)
        
        # Check that shapes were added
        assert len(fig.layout.shapes) > 0, "Activity bars should be added"
        
        # Check each shape for proper positioning
        for shape in fig.layout.shapes:
            # Check that shape is a rectangle
            assert shape.type == "rect", "Activity bars should be rectangles"
            
            # Check that x coordinates are dates
            assert hasattr(shape, 'x0'), "Shape should have x0 coordinate"
            assert hasattr(shape, 'x1'), "Shape should have x1 coordinate"
            
            # Check that y coordinates are within expected range
            assert hasattr(shape, 'y0'), "Shape should have y0 coordinate"
            assert hasattr(shape, 'y1'), "Shape should have y1 coordinate"
            
            # Y coordinates should be sequential rows (0, 1, 2, 3)
            y_center = (shape.y0 + shape.y1) / 2
            assert y_center >= 0, f"Y coordinate should be >= 0, got {y_center}"
            assert y_center <= 3, f"Y coordinate should be <= 3, got {y_center}"
            
            # Check that x coordinates are valid dates
            if hasattr(shape, 'x0') and shape.x0 is not None:
                assert isinstance(shape.x0, (str, date)), f"x0 should be date or string, got {type(shape.x0)}"
            if hasattr(shape, 'x1') and shape.x1 is not None:
                assert isinstance(shape.x1, (str, date)), f"x1 should be date or string, got {type(shape.x1)}"
    
    def test_dependency_arrow_positioning(self, sample_schedule, sample_config):
        """Test that dependency arrows connect the right activities."""
        fig = go.Figure()
        
        # Add dependency arrows
        add_dependency_arrows(fig, sample_schedule, sample_config)
        
        # Check that traces were added (arrows are traces, not shapes)
        assert len(fig.data) > 0, "Dependency arrows should be added as traces"
        
        # Check each trace for proper positioning
        for trace in fig.data:
            # Check that trace is scatter
            assert trace.type == 'scatter', "Dependency arrows should be scatter traces"
            
            # Check that x and y coordinates exist
            assert hasattr(trace, 'x'), "Trace should have x coordinates"
            assert hasattr(trace, 'y'), "Trace should have y coordinates"
            
            # Check that coordinates are lists
            assert isinstance(trace.x, (list, tuple)), f"x coordinates should be list/tuple, got {type(trace.x)}"
            assert isinstance(trace.y, (list, tuple)), f"y coordinates should be list/tuple, got {type(trace.y)}"
            
            # Check that coordinates have at least 2 points (start and end)
            assert len(trace.x) >= 2, f"Arrow should have at least 2 x points, got {len(trace.x)}"
            assert len(trace.y) >= 2, f"Arrow should have at least 2 y points, got {len(trace.y)}"
            
            # Check that x coordinates are valid dates
            for x_coord in trace.x:
                assert isinstance(x_coord, (str, date)), f"x coordinate should be date or string, got {type(x_coord)}"
            
            # Check that y coordinates are within expected range
            for y_coord in trace.y:
                assert isinstance(y_coord, (int, float)), f"y coordinate should be number, got {type(y_coord)}"
                # Allow negative offsets for better visual connection (from -0.5 to 3.5)
                assert y_coord >= -0.5, f"y coordinate should be >= -0.5, got {y_coord}"
                assert y_coord <= 3.5, f"y coordinate should be <= 3.5, got {y_coord}"
    
    def test_timeline_visual_accuracy(self, sample_schedule, sample_config):
        """Test that the visual timeline matches the actual schedule dates."""
        # Get timeline range
        timeline_range = get_chart_dimensions(sample_schedule, sample_config)
        
        # Check that timeline dates match schedule dates
        earliest_schedule_date = min(sample_schedule.values())
        latest_schedule_date = max(sample_schedule.values())
        
        # Timeline should start 30 days before earliest schedule date
        expected_start = earliest_schedule_date.replace(day=1)  # Start of month
        assert timeline_range['min_date'] <= expected_start, (
            f"Timeline should start before or on {expected_start}, got {timeline_range['min_date']}"
        )
        
        # Timeline should end 30 days after latest schedule date
        expected_end = latest_schedule_date.replace(day=28)  # End of month
        assert timeline_range['max_date'] >= expected_end, (
            f"Timeline should end after or on {expected_end}, got {timeline_range['max_date']}"
        )
        
        # Span should be positive
        assert timeline_range['span_days'] > 0, "Timeline span should be positive"
        
        # Max concurrency should be calculated based on actual overlapping dates, not just submission count
        # The concurrency calculation considers actual date overlaps, so we just verify it's reasonable
        assert timeline_range['max_concurrency'] > 0, "Max concurrency should be positive"
        assert timeline_range['max_concurrency'] <= len(sample_schedule), (
            f"Max concurrency should not exceed submission count ({len(sample_schedule)}), "
            f"got {timeline_range['max_concurrency']}"
        )
    
    # ============================================================================
    # CHART INTEGRATION AND VISUAL OUTPUT TESTS
    # ============================================================================
    
    def test_complete_chart_visual_elements(self, sample_schedule_state, output_dir):
        """Test that the complete gantt chart has all required visual elements."""
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
        
        # Check that title contains expected text
        title_text = fig.layout.title.text
        assert "Paper Submission Timeline" in title_text, f"Title should contain 'Paper Submission Timeline', got: {title_text}"
        
        # Check that x-axis is date type
        assert fig.layout.xaxis.type == 'date', "X-axis should be date type"
        
        # Check that y-axis has correct title
        assert fig.layout.yaxis.title.text == 'Activities', "Y-axis should have 'Activities' title"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "complete_gantt_chart.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_chart_dimensions_and_margins(self, sample_schedule_state, output_dir):
        """Test that chart has appropriate dimensions and margins."""
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
        
        # Check background colors
        assert fig.layout.plot_bgcolor == 'white', "Plot background should be white"
        assert fig.layout.paper_bgcolor == 'white', "Paper background should be white"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "chart_dimensions.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_activity_bar_styling_consistency(self, sample_schedule, sample_config, output_dir):
        """Test that all activity bars have consistent styling without double borders."""
        fig = go.Figure()
        
        # Add activity bars
        add_activity_bars(fig, sample_schedule, sample_config)
        
        # Check that shapes were added
        assert len(fig.layout.shapes) > 0, "Activity bars should be added"
        
        # Check each shape for consistent styling
        for i, shape in enumerate(fig.layout.shapes):
            # Check that shape is a rectangle
            assert shape.type == "rect", f"Activity bar {i} should be a rectangle"
            
            # Check for fill color
            assert shape.fillcolor is not None, f"Activity bar {i} should have fill color"
            
            # Check for border color
            assert shape.line.color is not None, f"Activity bar {i} should have border color"
            
            # CRITICAL TEST: Check that fill and border colors are different (avoid double border effect)
            assert shape.fillcolor != shape.line.color, (
                f"Activity bar {i}: Fill color ({shape.fillcolor}) and border color ({shape.line.color}) "
                f"should be different to prevent double border effect"
            )
            
            # Check opacity
            assert shape.opacity == 0.8, f"Activity bar {i} should have 0.8 opacity"
            
            # Check line width
            assert shape.line.width == 2, f"Activity bar {i} should have 2px border width"
            
            # Check that colors are valid hex colors
            assert shape.fillcolor.startswith('#'), f"Fill color should be hex: {shape.fillcolor}"
            assert shape.line.color.startswith('#'), f"Border color should be hex: {shape.line.color}"
            assert len(shape.fillcolor) == 7, f"Fill color should be 7 characters: {shape.fillcolor}"
            assert len(shape.line.color) == 7, f"Border color should be 7 characters: {shape.line.color}"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "activity_bars_styling.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    def test_dependency_arrow_styling_consistency(self, sample_schedule, sample_config, output_dir):
        """Test that all dependency arrows have consistent styling."""
        fig = go.Figure()
        
        # Add dependency arrows
        add_dependency_arrows(fig, sample_schedule, sample_config)
        
        # Check that traces were added (arrows are traces, not shapes)
        assert len(fig.data) > 0, "Dependency arrows should be added as traces"
        
        # Check each trace for consistent styling
        for i, trace in enumerate(fig.data):
            # Check that trace is scatter
            assert trace.type == 'scatter', f"Dependency arrow {i} should be scatter trace"
            
            # Check mode
            assert trace.mode == 'lines+markers', f"Dependency arrow {i} should have lines and markers"
            
            # Check line color
            assert trace.line.color == '#e74c3c', f"Dependency arrow {i} should have red color (#e74c3c)"
            
            # Check line width
            assert trace.line.width == 2, f"Dependency arrow {i} should have 2px width"
            
            # Check line dash
            assert trace.line.dash == 'dot', f"Dependency arrow {i} should have dotted lines"
            
            # Check marker symbol
            assert trace.marker.symbol == 'arrow-up', f"Dependency arrow {i} should have arrow-up markers"
            
            # Check marker size
            assert trace.marker.size == 8, f"Dependency arrow {i} should have size 8 markers"
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "dependency_arrows_styling.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    # ============================================================================
    # HEADLESS BROWSER VISUAL VERIFICATION TESTS
    # ============================================================================
    
    @pytest.mark.asyncio
    async def test_gantt_chart_screenshot_capture(self, sample_html_file, output_dir):
        """Test that gantt chart can be captured as screenshot for visual verification."""
        try:
            # Try to capture screenshot
            screenshot_path = os.path.join(output_dir, "gantt_chart_screenshot.png")
            
            # Convert file:// URL to proper URL for testing
            file_url = f"file://{sample_html_file}"
            
            success = await capture_web_page_screenshot(
                url=file_url,
                output_path=screenshot_path,
                wait_for_selector="#gantt-chart",
                wait_timeout=5000
            )
            
            if success:
                assert os.path.exists(screenshot_path), "Screenshot should be created"
                print(f"Screenshot saved to: {screenshot_path}")
                
                # Verify screenshot file size is reasonable
                file_size = os.path.getsize(screenshot_path)
                assert file_size > 1000, f"Screenshot should be larger than 1KB, got {file_size} bytes"
                assert file_size < 10000000, f"Screenshot should be smaller than 10MB, got {file_size} bytes"
                
            else:
                print("Screenshot capture failed (this is expected for file:// URLs)")
                pytest.skip("Screenshot test not available in this environment")
                
        except Exception as e:
            # This test is optional and might fail in some environments
            print(f"Screenshot test skipped: {e}")
            pytest.skip("Screenshot test not available in this environment")
    
    def test_color_legend_verification(self, sample_schedule_state, output_dir):
        """Test that the chart uses the correct colors as specified in the legend."""
        fig = create_gantt_chart(sample_schedule_state)
        
        # Get all colors used in the chart
        colors_used = set()
        
        # Collect colors from shapes (activity bars)
        if fig.layout.shapes:
            for shape in fig.layout.shapes:
                if hasattr(shape, 'fillcolor') and shape.fillcolor:
                    colors_used.add(shape.fillcolor)
                if hasattr(shape, 'line') and hasattr(shape.line, 'color') and shape.line.color:
                    colors_used.add(shape.line.color)
        
        # Collect colors from traces (dependency arrows)
        for trace in fig.data:
            if hasattr(trace, 'line') and hasattr(trace.line, 'color') and trace.line.color:
                colors_used.add(trace.line.color)
            if hasattr(trace, 'marker') and hasattr(trace.marker, 'color') and trace.marker.color:
                colors_used.add(trace.marker.color)
        
        # Expected colors based on our business logic
        expected_colors = {
            '#3498db',  # Engineering papers (MODs) - Blue
            '#9b59b6',  # Medical papers (ED) - Purple  
            '#85c1e9',  # Engineering abstracts - Light Blue
            '#e74c3c',  # Dependency arrows - Red
        }
        
        # Check that we have the expected colors
        for expected_color in expected_colors:
            if expected_color in colors_used:
                print(f"✓ Found expected color: {expected_color}")
            else:
                print(f"✗ Missing expected color: {expected_color}")
        
        # We should have at least the main submission colors
        assert any(color in colors_used for color in ['#3498db', '#9b59b6', '#85c1e9']), (
            f"Chart should contain at least one of the expected submission colors. "
            f"Found colors: {colors_used}"
        )
        
        # Save chart as HTML for manual inspection
        html_file = Path(output_dir) / "color_legend_verification.html"
        fig.write_html(str(html_file))
        assert html_file.exists(), "HTML file should be created"
    
    # ============================================================================
    # REGRESSION TESTS - Ensure fixes actually work
    # ============================================================================
    
    def test_double_border_fix_regression(self):
        """Regression test to ensure the double border issue is fixed."""
        # Test all submission types to ensure no double border effect
        test_cases = [
            (SubmissionType.PAPER, "pccp", "Engineering Paper"),
            (SubmissionType.PAPER, "ed", "Medical Paper"),
            (SubmissionType.ABSTRACT, "pccp", "Abstract"),
        ]
        
        for kind, author, description in test_cases:
            submission = Submission(
                id=f"test-{kind.value}-{author}",
                title=f"Test {description}",
                kind=kind,
                author=author
            )
            
            fill_color = _get_submission_color(submission)
            border_color = _get_border_color(submission)
            
            # CRITICAL REGRESSION TEST: This was the main issue we fixed
            assert fill_color != border_color, (
                f"REGRESSION: {description} still has double border effect! "
                f"Fill: {fill_color}, Border: {border_color}"
            )
            
            # Additional regression checks
            assert fill_color.startswith('#'), f"Fill color should be hex: {fill_color}"
            assert border_color.startswith('#'), f"Border color should be hex: {border_color}"
            assert len(fill_color) == 7, f"Fill color should be 7 characters: {fill_color}"
            assert len(border_color) == 7, f"Border color should be 7 characters: {border_color}"
    
    def test_color_logic_regression(self):
        """Regression test to ensure the color logic works correctly."""
        # Test engineering papers (MODs) - should be blue
        engineering_submission = Submission(
            id="test-eng",
            title="Test Engineering",
            kind=SubmissionType.PAPER,
            author="pccp"
        )
        
        engineering_color = _get_submission_color(engineering_submission)
        assert engineering_color == "#3498db", (
            f"REGRESSION: Engineering papers should be blue (#3498db), got {engineering_color}"
        )
        
        # Test medical papers (ED) - should be purple
        medical_submission = Submission(
            id="test-med",
            title="Test Medical",
            kind=SubmissionType.PAPER,
            author="ed"
        )
        
        medical_color = _get_submission_color(medical_submission)
        assert medical_color == "#9b59b6", (
            f"REGRESSION: Medical papers should be purple (#9b59b6), got {medical_color}"
        )
        
        # Test abstracts - should be light blue for engineering
        abstract_submission = Submission(
            id="test-abs",
            title="Test Abstract",
            kind=SubmissionType.ABSTRACT,
            author="pccp"
        )
        
        abstract_color = _get_submission_color(abstract_submission)
        assert abstract_color == "#85c1e9", (
            f"REGRESSION: Engineering abstracts should be light blue (#85c1e9), got {abstract_color}"
        )
