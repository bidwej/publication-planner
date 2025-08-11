"""
Interactive Gantt chart component for schedule visualization.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import plotly.graph_objects as go

from src.core.models import Config, Submission
from app.components.charts.gantt_formatter import GanttFormatter

class GanttChartBuilder:
    """Builder class for creating Gantt charts with proper separation of concerns."""
    
    def __init__(self, schedule: Dict[str, date], config: Config):
        self.schedule = schedule
        self.config = config
        self.min_date = min(schedule.values()) if schedule else date.today()
        self.max_date = max(schedule.values()) + timedelta(days=90) if schedule else date.today()
        self.fig = go.Figure()
        
        # Initialize Gantt formatter with consistent date names
        self.gantt_formatter = GanttFormatter(self.min_date, self.max_date)
    
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
        """Add submission bars showing concurrency levels."""
        submissions_dict = self.config.submissions_dict
        
        # Get sorted schedule for consistent ordering
        sorted_schedule = self._get_sorted_schedule()
        
        # Calculate concurrency levels for each paper
        concurrency_map = self._calculate_concurrency_levels(sorted_schedule)
        
        # Add bars at their concurrency levels
        for submission_id, start_date in sorted_schedule:
            submission = submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Get concurrency level for this paper
            concurrency_level = concurrency_map.get(submission_id, 0)
            
            # Calculate duration
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7  # Minimum 1 week for work items
            
            start_day = (start_date - self.min_date).days
            end_day = start_day + duration_days
            
            # Create the bar at the concurrency level
            bar_height = 0.3
            y_pos = concurrency_level
            self.fig.add_shape(
                type="rect",
                x0=start_day,
                x1=end_day,
                y0=y_pos - bar_height,
                y1=y_pos + bar_height,
                fillcolor=self._get_submission_color(submission),
                line=dict(color="black", width=1),
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
    
    def _calculate_concurrency_levels(self, sorted_schedule):
        """Calculate concurrency level for each submission to avoid overlaps."""
        concurrency_map = {}
        active_papers = []  # List of (end_date, submission_id) tuples
        
        for submission_id, start_date in sorted_schedule:
            submission = self.config.submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Calculate end date
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7
            end_date = start_date + timedelta(days=duration_days)
            
            # Remove completed papers from active list
            active_papers = [(end, sid) for end, sid in active_papers if end > start_date]
            
            # Find available concurrency level
            concurrency_level = 0
            while any(concurrency_level == self._get_concurrency_level(sid, start_date, end_date, concurrency_map) 
                     for _, sid in active_papers):
                concurrency_level += 1
            
            # Assign concurrency level
            concurrency_map[submission_id] = concurrency_level
            
            # Add to active papers
            active_papers.append((end_date, submission_id))
        
        return concurrency_map
    
    def _get_concurrency_level(self, submission_id, start_date, end_date, concurrency_map):
        """Get the concurrency level for a specific submission at a given time."""
        if submission_id not in concurrency_map:
            return -1
        
        # Check if this submission overlaps with the time period
        submission = self.config.submissions_dict.get(submission_id)
        if not submission:
            return -1
        
        sub_duration = submission.get_duration_days(self.config)
        if sub_duration <= 0:
            sub_duration = 7
        
        sub_start = start_date
        sub_end = sub_start + timedelta(days=sub_duration)
        
        # Check for overlap
        if start_date < sub_end and end_date > sub_start:
            return concurrency_map[submission_id]
        
        return -1
    
    def _add_blackout_periods(self):
        """Add blackout period backgrounds with proper light gray coloring."""
        blackout_data = self._load_blackout_data()
        
        # Calculate maximum concurrency for Y-axis range
        max_concurrency = 0
        if self.schedule:
            concurrency_map = self._calculate_concurrency_levels(self._get_sorted_schedule())
            max_concurrency = max(concurrency_map.values()) if concurrency_map else 0
        
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
                    y0=0,
                    y1=max_concurrency + 1,
                    fillcolor="rgba(200, 200, 200, 0.2)",  # Light gray
                    line=dict(width=0),
                    layer="below"
                )
        
        # Add weekend periods
        if blackout_data.get('weekends', {}).get('enabled', False):
            self._add_weekend_periods(max_concurrency)
        
        # Add holiday periods
        self._add_holiday_periods(blackout_data, max_concurrency)
        
        # Add time interval bands (monthly/quarterly)
        self._add_time_interval_bands(max_concurrency)
    
    def _add_weekend_periods(self, max_concurrency):
        """Add weekend periods as recurring shaded rectangles."""
        current_date = self.min_date
        while current_date <= self.max_date:
            if current_date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                day_offset = (current_date - self.min_date).days
                
                self.fig.add_shape(
                    type="rect",
                    x0=day_offset,
                    x1=day_offset + 1,
                    y0=0,
                    y1=max_concurrency + 1,
                    fillcolor="rgba(200, 200, 200, 0.2)",
                    line=dict(width=0),
                    layer="below"
                )
            
            current_date += timedelta(days=1)
    
    def _add_holiday_periods(self, blackout_data, max_concurrency):
        """Add federal holiday periods."""
        holiday_dates = set()
        
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
                            y0=0,
                            y1=max_concurrency + 1,
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            line=dict(width=0),
                            layer="below"
                        )
                except ValueError:
                    continue
    
    def _add_time_interval_bands(self, max_concurrency):
        """Add alternating time interval bands for better readability."""
        # Calculate timeline duration
        timeline_days = (self.max_date - self.min_date).days
        
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
                y0=0,
                y1=max_concurrency + 1,
                fillcolor=fillcolor,
                line=dict(width=0),
                layer="below"
            )
            
            current_day = end_day
            band_count += 1
    
    def _add_dependency_arrows(self):
        """Add dependency arrows between submissions using concurrency levels."""
        submissions_dict = self.config.submissions_dict
        
        # Calculate concurrency levels for positioning
        concurrency_map = self._calculate_concurrency_levels(self._get_sorted_schedule())
        
        arrow_count = 0
        max_arrows = 20  # Limit arrows to avoid performance issues
        
        for submission_id, start_date in self.schedule.items():
            if arrow_count >= max_arrows:
                break
                
            submission = submissions_dict.get(submission_id)
            if not submission or not submission.depends_on:
                continue
            
            # Get concurrency level for this submission
            current_concurrency = concurrency_map.get(submission_id, 0)
            
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
                        dep_concurrency = concurrency_map.get(dep_id, 0)
                        
                        # Add arrow from dependency end to current start
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
        
        # Calculate maximum concurrency level needed
        max_concurrency = 0
        if self.schedule:
            concurrency_map = self._calculate_concurrency_levels(self._get_sorted_schedule())
            max_concurrency = max(concurrency_map.values()) if concurrency_map else 0
        
        # Y-axis should show concurrency levels (0, 1, 2, 3, etc.)
        y_labels = [str(i) for i in range(max_concurrency + 1)]
        
        # Update layout with concurrency-based Y-axis
        self.fig.update_layout(
            title={
                'text': 'Paper Submission Timeline (Concurrency View)',
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
                'tickvals': list(range(max_concurrency + 1)),
                'ticktext': y_labels,
                'tickangle': 0,
                'tickfont': {'size': 10},
                'range': [-0.5, max_concurrency + 0.5]
            },
            margin=self.gantt_formatter.get_margin_config(),
            height=max(600, (max_concurrency + 1) * 40),  # Dynamic height based on concurrency
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
            if submission_id.startswith('mod_'):
                return f"MOD {self._extract_mod_number(submission_id)}"
            else:
                return submission_id.replace('_', ' ').title()
        elif submission.author == "ed":
            # For ED Papers, just show the number from the ID
            if submission_id.startswith('J'):
                return f"ED Paper {self._extract_ed_number(submission_id)}"
            else:
                return submission_id.replace('_', ' ').title()
        else:
            # For other submissions, use a clean version
            return submission_id.replace('_', ' ').title()
    
    def _get_submission_color(self, submission: Submission) -> str:
        """Get color based on submission author (PCCP vs ED)."""
        # Use the existing author field - much cleaner!
        if submission.author == "pccp":
            return "#2E86AB"  # Blue for PCCP (MODs)
        elif submission.author == "ed":
            return "#A23B72"  # Purple for ED Papers
        else:
            # Default colors for other types
            if submission.kind.value == "paper":
                return "#F18F01"  # Orange for other papers
            else:
                return "#C73E1D"  # Red for work items
    
    def _get_conference_info(self, submission: Submission) -> str:
        """Get simplified conference info - just the type, not the venue name."""
        # Don't show conference names - just show if it's a paper or work item
        if submission.kind.value == "paper":
            return "Paper"
        else:
            return "Work Item"
    
    def _add_legend(self):
        """Add a legend to explain the color coding."""
        legend_items = [
            ("MOD Papers", "#2E86AB"),
            ("ED Papers", "#A23B72"),
            ("Other Papers", "#F18F01"),
            ("Work Items", "#C73E1D")
        ]
        
        for i, (label, color) in enumerate(legend_items):
            self.fig.add_annotation(
                x=0.02,
                y=0.95 - i * 0.05,
                text=f"<span style='color:{color}'>■</span> {label}",
                showarrow=False,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                font=dict(size=10),
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
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

def create_gantt_chart(schedule: Dict[str, date], config: Config) -> go.Figure:
    """Create an interactive Gantt chart for the schedule."""
    builder = GanttChartBuilder(schedule, config)
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
