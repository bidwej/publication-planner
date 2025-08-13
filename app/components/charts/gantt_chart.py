"""
Interactive Gantt chart component for schedule visualization.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import plotly.graph_objects as go

from src.core.models import Config, Submission
from src.analytics.formatters.dates import format_month_year
from app.components.charts.gantt_formatter import GanttFormatter, GanttStyler

class GanttChartBuilder:
    """Builder class for creating Gantt charts with proper separation of concerns."""
    
    def __init__(self, schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None):
        self.schedule = schedule
        self.config = config
        
        # Handle forced timeline range if specified
        if forced_timeline and forced_timeline.get("force_timeline_range"):
            self.min_date = forced_timeline["timeline_start"]
            self.max_date = forced_timeline["timeline_end"]
            # CRITICAL: When using forced timeline, bars must be positioned relative to timeline start
            self.timeline_start = forced_timeline["timeline_start"]
        else:
            # Calculate dates naturally from schedule
            self.min_date = min(schedule.values()) if schedule else date.today()
            # Calculate max_date more precisely - find the actual end of the last submission
            if schedule:
                max_start = max(schedule.values())
                # Find the submission with the latest end date
                max_end_date = max_start
                for submission_id, start_date in schedule.items():
                    submission = config.submissions_dict.get(submission_id)
                    if submission:
                        duration = submission.get_duration_days(config)
                        if duration <= 0:
                            duration = 7
                        end_date = start_date + timedelta(days=duration)
                        if end_date > max_end_date:
                            max_end_date = end_date
                
                # Add a small buffer (30 days instead of 90) for visual spacing
                self.max_date = max_end_date + timedelta(days=30)
            else:
                self.max_date = date.today()
            # For natural timeline, timeline start = min_date
            self.timeline_start = self.min_date
        
        self.fig = go.Figure()
        
        # Initialize Gantt formatter with EXACTLY the same date range used for bar positioning
        # This ensures timeline ticks align perfectly with bar positions
        self.gantt_formatter = GanttFormatter(self.min_date, self.max_date)
        
        # Calculate concurrency levels once upfront - simple and logical
        self.concurrency_map = {}
        self.max_concurrency = 0
        if self.schedule:
            self.concurrency_map = self._calculate_simple_concurrency()
            self.max_concurrency = max(self.concurrency_map.values()) if self.concurrency_map else 0
    
    def _calculate_simple_concurrency(self) -> Dict[str, int]:
        """Calculate concurrency levels simply: start at row 0, only go to row 1 if overlap."""
        concurrency_map = {}
        
        # Sort submissions by start date to process them chronologically
        sorted_schedule = sorted(self.schedule.items(), key=lambda x: x[1])
        
        for submission_id, start_date in sorted_schedule:
            submission = self.config.submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Calculate end date
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7  # Minimum 1 week for work items
            end_date = start_date + timedelta(days=duration_days)
            
            # Find the lowest available row (start at 0)
            row = 0
            while self._row_has_overlap(row, start_date, end_date, submission_id, concurrency_map):
                row += 1
            
            concurrency_map[submission_id] = row
        
        return concurrency_map
    
    def _row_has_overlap(self, row: int, start_date: date, end_date: date, 
                         current_id: str, concurrency_map: Dict[str, int]) -> bool:
        """Check if a specific row has overlap with the current submission."""
        for other_id, other_row in concurrency_map.items():
            if other_id == current_id:
                continue
            
            if other_row != row:
                continue
            
            # Check if there's time overlap
            other_submission = self.config.submissions_dict.get(other_id)
            if not other_submission:
                continue
            
            other_start = self.schedule[other_id]
            other_duration = other_submission.get_duration_days(self.config)
            if other_duration <= 0:
                other_duration = 7
            
            other_end = other_start + timedelta(days=other_duration)
            
            # Check for overlap: two submissions overlap if one starts before the other ends
            # and the other starts before the first ends
            if start_date < other_end and end_date > other_start:
                return True
        
        return False
    
    def _get_sorted_schedule(self):
        """Get submissions sorted by author (PCCP, then ED, then others), then by ID number."""
        def sort_key(item):
            submission_id = item[0]
            submission = self.config.submissions_dict.get(submission_id)
            if not submission:
                return (2, submission_id)
            
            # Use the existing author field - much cleaner!
            if submission.author == "pccp":
                # For MODs, sort by the number in the ID
                return (0, self._extract_mod_number(submission_id))
            elif submission.author == "ed":
                # For ED Papers, sort by the number in the ID
                return (1, self._extract_ed_number(submission_id))
            else:
                return (2, submission_id)  # Others last
        
        return sorted(self.schedule.items(), key=sort_key)
    
    def _extract_mod_number(self, submission_id: str) -> int:
        """Extract the number from a MOD ID (e.g., 'mod_1' -> 1)."""
        if submission_id.startswith('mod_'):
            try:
                return int(submission_id[4:])
            except ValueError:
                return 0
        return 0
    
    def _extract_ed_number(self, submission_id: str) -> int:
        """Extract the number from an ED Paper ID (e.g., 'J1' -> 1)."""
        if submission_id.startswith('J'):
            try:
                return int(submission_id[1:])
            except ValueError:
                return 0
        return 0
    
    def build(self) -> go.Figure:
        """Build the complete Gantt chart."""
        if not self.schedule:
            return self._create_empty_chart()
        
        self._add_submission_bars()
        self._add_blackout_periods()
        self._add_dependency_arrows()
        self._configure_layout()
        self._add_legend()
        
        return self.fig
    
    def _add_submission_bars(self):
        """Add submission bars showing concurrency levels with proper styling and borders."""
        submissions_dict = self.config.submissions_dict
        
        # Get sorted schedule for consistent ordering
        sorted_schedule = self._get_sorted_schedule()
        
        # Add bars at their concurrency levels
        for submission_id, start_date in sorted_schedule:
            submission = submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Get concurrency level for this paper
            concurrency_level = self.concurrency_map.get(submission_id, 0)
            
            # Calculate duration
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7  # Minimum 1 week for work items
            
            start_day = (start_date - self.timeline_start).days
            end_day = start_day + duration_days
            
            # Get colors and borders from the styler
            base_color = GanttStyler.get_submission_color(submission)
            border_color = GanttStyler.get_border_color(submission, self.config)
            matching_border_color = GanttStyler.get_matching_border_color(submission, self.config)
            
            # Use matching border color if available (for abstract-paper pairs)
            final_border_color = matching_border_color or border_color or "black"
            border_width = 3 if matching_border_color else (2 if border_color else 1)
            
            # Create the bar at the concurrency level with proper proportions
            bar_height = 0.8  # Increased from 0.3 for better visibility
            y_pos = concurrency_level
            self.fig.add_shape(
                type="rect",
                x0=start_day,
                x1=end_day,
                y0=y_pos - bar_height/2,  # Center the bar on the concurrency level
                y1=y_pos + bar_height/2,
                fillcolor=base_color,
                line=dict(color=final_border_color, width=border_width),
                layer="above"
            )
            
            # Add text label on the bar
            display_title = self._get_display_title(submission, submission_id)
            self.fig.add_annotation(
                x=start_day + (end_day - start_day) / 2,  # Center of bar
                y=y_pos,
                text=display_title,
                showarrow=False,
                xanchor="center",
                yanchor="middle",
                font=dict(size=8, color="white"),
                bgcolor="rgba(0, 0, 0, 0.7)",
                bordercolor="white",
                borderwidth=1
            )
    
    def _add_blackout_periods(self):
        """Add blackout period backgrounds with proper light gray coloring."""
        blackout_data = self._load_blackout_data()
        
        # Calculate proper Y-axis range based on bar height
        bar_height = 0.8
        y_margin = bar_height / 2 + 0.2
        
        # Add custom blackout periods
        custom_periods = blackout_data.get('custom_blackout_periods', [])
        for period in custom_periods:
            start_date = date.fromisoformat(period['start'])
            end_date = date.fromisoformat(period['end'])
            
            if start_date <= self.max_date and end_date >= self.min_date:
                start_days = max(0, (start_date - self.min_date).days)
                end_days = (end_date - self.min_date).days
                
                self.fig.add_shape(
                    type="rect",
                    x0=start_days,
                    x1=end_days,
                    y0=-y_margin,
                    y1=self.max_concurrency + y_margin,
                    fillcolor="rgba(200, 200, 200, 0.2)",  # Light gray
                    line=dict(width=0),
                    layer="below"
                )
        
        # Add weekend periods
        if blackout_data.get('weekends', {}).get('enabled', False):
            self._add_weekend_periods()
        
        # Add holiday periods
        self._add_holiday_periods(blackout_data)
        
        # Add time interval bands (monthly/quarterly)
        self._add_time_interval_bands()
    
    def _add_weekend_periods(self):
        """Add weekend periods as recurring shaded rectangles."""
        current_date = self.min_date
        
        # Calculate proper Y-axis range based on bar height
        bar_height = 0.8
        y_margin = bar_height / 2 + 0.2
        
        while current_date <= self.max_date:
            if current_date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                day_offset = (current_date - self.min_date).days
                
                self.fig.add_shape(
                    type="rect",
                    x0=day_offset,
                    x1=day_offset + 1,
                    y0=-y_margin,
                    y1=self.max_concurrency + y_margin,
                    fillcolor="rgba(200, 200, 200, 0.2)",
                    line=dict(width=0),
                    layer="below"
                )
            
            current_date += timedelta(days=1)
    
    def _add_holiday_periods(self, blackout_data):
        """Add federal holiday periods."""
        holiday_dates = set()
        
        # Calculate proper Y-axis range based on bar height
        bar_height = 0.8
        y_margin = bar_height / 2 + 0.2
        
        # Use current year and next year for holiday generation
        current_year = date.today().year
        for year in [str(current_year), str(current_year + 1)]:
            holidays = blackout_data.get(f'federal_holidays_{year}', [])
            for holiday_str in holidays:
                holiday_date = date.fromisoformat(holiday_str)
                holiday_dates.add((holiday_date.month, holiday_date.day))
        
        start_year = self.min_date.year
        end_year = self.max_date.year
        
        for year in range(start_year, end_year + 1):
            for month, day in holiday_dates:
                try:
                    holiday_date = date(year, month, day)
                    if self.min_date <= holiday_date <= self.max_date:
                        day_offset = (holiday_date - self.min_date).days
                        
                        self.fig.add_shape(
                            type="rect",
                            x0=day_offset,
                            x1=day_offset + 1,
                            y0=-y_margin,
                            y1=self.max_concurrency + y_margin,
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            line=dict(width=0),
                            layer="below"
                        )
                except ValueError:
                    continue
    
    def _add_time_interval_bands(self):
        """Add alternating time interval bands for better readability."""
        # Calculate timeline duration
        timeline_days = (self.max_date - self.min_date).days
        
        # Calculate proper Y-axis range based on bar height
        bar_height = 0.8
        y_margin = bar_height / 2 + 0.2
        
        # Use larger intervals to prevent performance issues
        if timeline_days <= 90:  # 3 months or less
            interval_days = 14  # Bi-weekly
        elif timeline_days <= 365:  # 1 year or less
            interval_days = 60  # Bi-monthly
        else:  # More than 1 year
            interval_days = 120  # Quarterly
        
        # Add alternating bands with strict limit
        current_day = 0
        band_count = 0
        max_bands = 12  # Strict limit to prevent hanging
        
        while current_day <= timeline_days and band_count < max_bands:
            end_day = min(current_day + interval_days, timeline_days)
            
            # Alternate colors for bands
            if band_count % 2 == 0:
                fillcolor = "rgba(240, 240, 240, 0.1)"  # Very light gray
            else:
                fillcolor = "rgba(255, 255, 255, 0.0)"  # Transparent
            
            self.fig.add_shape(
                type="rect",
                x0=current_day,
                x1=end_day,
                y0=-y_margin,
                y1=self.max_concurrency + y_margin,
                fillcolor=fillcolor,
                line=dict(width=0),
                layer="below"
            )
            
            current_day = end_day
            band_count += 1
    
    def _add_dependency_arrows(self):
        """Add dependency arrows between submissions using concurrency levels."""
        submissions_dict = self.config.submissions_dict
        
        arrow_count = 0
        max_arrows = 20  # Limit arrows to avoid performance issues
        
        for submission_id, start_date in self.schedule.items():
            if arrow_count >= max_arrows:
                break
                
            submission = submissions_dict.get(submission_id)
            if not submission or not submission.depends_on:
                continue
            
            # Get concurrency level for this submission
            current_concurrency = self.concurrency_map.get(submission_id, 0)
            
            for dep_id in submission.depends_on:
                if arrow_count >= max_arrows:
                    break
                    
                if dep_id in self.schedule:
                    dep_start = self.schedule[dep_id]
                    dep_submission = submissions_dict.get(dep_id)
                    if dep_submission:
                        dep_duration = dep_submission.get_duration_days(self.config)
                        if dep_duration <= 0:
                            dep_duration = 7  # Minimum duration for work items
                        dep_end_days = (dep_start + timedelta(days=dep_duration) - self.min_date).days
                        current_start_days = (start_date - self.min_date).days
                        
                        # Get concurrency level for the dependency
                        dep_concurrency = self.concurrency_map.get(dep_id, 0)
                        
                        # Add arrow from dependency end to current start
                        # Use concurrency levels directly as Y coordinates
                        self.fig.add_annotation(
                            x=dep_end_days,
                            y=dep_concurrency,
                            xref="x",
                            yref="y",
                            axref="x",
                            ayref="y",
                            ax=current_start_days,
                            ay=current_concurrency,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor="gray"
                        )
                        arrow_count += 1
    
    def _configure_layout(self):
        """Configure the chart layout with concurrency-based Y-axis."""
        # Primary x-axis (quarters) - on bottom
        primary_axis_config = self.gantt_formatter.get_axis_config()
        
        # Get year annotations to place below the axis
        year_annotations = self.gantt_formatter.get_year_annotations()
        
        # Create a nice title with date range - using user's preferred format
        start_month = self.min_date.strftime("%b")
        end_month = self.max_date.strftime("%b")
        start_year = self.min_date.year
        end_year = self.max_date.year
        
        if start_year == end_year:
            if start_month == end_month:
                title_text = f"Paper Submission Timeline: {start_month} {start_year}"
            else:
                title_text = f"Paper Submission Timeline: {start_month} to {end_month}, {start_year}"
        else:
            title_text = f"Paper Submission Timeline: {start_month} {start_year} - {end_month} {end_year}"
        
        # Y-axis should show concurrency levels (0, 1, 2, 3, etc.)
        y_labels = [str(i) for i in range(self.max_concurrency + 1)]
        
        # Calculate proper Y-axis range based on bar height
        bar_height = 0.8
        y_margin = bar_height / 2 + 0.2  # Small margin around bars
        
        # Update layout with concurrency-based Y-axis
        self.fig.update_layout(
            title={
                'text': title_text,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            xaxis=primary_axis_config,
            yaxis={
                'title': 'Concurrency Level',
                'showgrid': True,
                'gridcolor': 'lightgray',
                'tickmode': 'array',
                'tickvals': list(range(self.max_concurrency + 1)),
                'ticktext': y_labels,
                'tickangle': 0,
                'tickfont': {'size': 10},
                'range': [-y_margin, self.max_concurrency + y_margin]  # Proper scaling
            },
            margin=self.gantt_formatter.get_margin_config(),
            height=max(600, (self.max_concurrency + 1) * 60),  # Increased height per row
            showlegend=True,
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1
            }
        )
        
        # Add year annotations
        for annotation in year_annotations:
            self.fig.add_annotation(annotation)
    
    def _get_display_title(self, submission: Submission, submission_id: str) -> str:
        """Get a clean, simple display title for the chart."""
        # Use the existing author field - no need to parse IDs!
        if submission.author == "pccp":
            # For MODs, just show the number from the ID
            return f"MOD {self._extract_mod_number(submission_id)}"
        elif submission.author == "ed":
            # For ED Papers, just show the number from the ID
            return f"ED Paper {self._extract_ed_number(submission_id)}"
        else:
            # For other submissions, use a clean version
            return submission_id.replace('_', ' ').title()
    
    def _add_legend(self):
        """Add a comprehensive legend explaining all the styling."""
        legend_items = GanttStyler.get_legend_items()
        
        for i, (label, color, description) in enumerate(legend_items):
            # Position legend on the left side
            x_pos = 0.02
            y_pos = 0.95 - i * 0.06
            
            # For border items, show a border instead of a filled square
            if "Border" in label:
                # Show border example
                self.fig.add_annotation(
                    x=x_pos,
                    y=y_pos,
                    text=f"<span style='color:{color}'>▢</span> {label}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    xanchor="left",
                    yanchor="top",
                    font=dict(size=10),
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="black",
                    borderwidth=1
                )
            else:
                # Show filled square for submission types
                self.fig.add_annotation(
                    x=x_pos,
                    y=y_pos,
                    text=f"<span style='color:{color}'>■</span> {label}",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    xanchor="left",
                    yanchor="top",
                    font=dict(size=10),
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="black",
                    borderwidth=1
                )
            
            # Add description below the label
            self.fig.add_annotation(
                x=x_pos + 0.15,
                y=y_pos,
                text=f"({description})",
                showarrow=False,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                font=dict(size=8, color="gray"),
                bgcolor="rgba(255, 255, 255, 0.7)",
                bordercolor="lightgray",
                borderwidth=1
            )
    
    def _load_blackout_data(self) -> Dict:
        """Load blackout data from file."""
        try:
            blackout_path = Path('data/blackout.json')
            if blackout_path.exists():
                with open(blackout_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print("Warning: Could not load blackout data: %s", e)
        return {}
    
    def _create_empty_chart(self) -> go.Figure:
        """Create an empty chart."""
        fig = go.Figure()
        fig.update_layout(
            title={'text': 'No Schedule Available', 'x': 0.5, 'xanchor': 'center'},
            xaxis=dict(title='Timeline (Days)'),
            yaxis=dict(title='Submissions'),
            height=600,
            plot_bgcolor='white',
            paper_bgcolor='white',
            annotations=[{
                'text': 'Generate a schedule to see the timeline',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': 'gray'}
            }]
        )
        return fig

def create_gantt_chart(schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None) -> go.Figure:
    """Create an interactive Gantt chart for the schedule."""
    builder = GanttChartBuilder(schedule, config, forced_timeline)
    return builder.build()

def generate_gantt_png(schedule: Dict[str, date], config: Config, filename: str = "chart_current.png") -> str:
    """Generate a PNG file of the Gantt chart with the specified filename."""
    try:
        fig = create_gantt_chart(schedule, config)
        
        # For Plotly, we need to use write_image with proper settings
        # This requires kaleido or orca to be installed
        fig.write_image(
            filename, 
            width=1200, 
            height=600, 
            scale=2,
            format='png'
        )
        
        print("✅ Gantt chart saved as %s", filename)
        return filename
    except ImportError as e:
        print("❌ Missing dependency for PNG generation: %s", e)
        print("💡 Install kaleido: pip install kaleido")
        return ""
    except Exception as e:
        print("❌ Error generating PNG: %s", e)
        return ""
