"""
Interactive Gantt chart component for schedule visualization.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import plotly.graph_objects as go

from src.core.models import Config, Submission, SubmissionType
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
        """Add submission bars using proper Gantt chart shapes."""
        submissions_dict = self.config.submissions_dict
        
        # Sort submissions by start date for consistent ordering
        sorted_schedule = sorted(self.schedule.items(), key=lambda x: x[1])
        
        for i, (submission_id, start_date) in enumerate(sorted_schedule):
            submission = submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Work items should have a minimum duration for visibility
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7  # Minimum 1 week for work items
            
            start_day = (start_date - self.min_date).days
            end_day = start_day + duration_days
            
            # Create the bar as a shape with proper spacing
            bar_height = 0.4
            y_pos = i
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
            
            # Add text label outside the bar
            display_title = self._get_display_title(submission, submission_id)
            conference_info = self._get_conference_info(submission)
            
            # Position label to the left of the bar
            self.fig.add_annotation(
                x=start_day - 5,  # 5 days to the left
                y=y_pos,
                text=f"{display_title}<br>{conference_info}",
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(size=9, color="black"),
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="black",
                borderwidth=1
            )
    
    def _add_blackout_periods(self):
        """Add blackout period backgrounds with proper light gray coloring."""
        blackout_data = self._load_blackout_data()
        
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
                    y1=len(self.schedule),
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
        while current_date <= self.max_date:
            if current_date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                day_offset = (current_date - self.min_date).days
                
                self.fig.add_shape(
                    type="rect",
                    x0=day_offset,
                    x1=day_offset + 1,
                    y0=0,
                    y1=len(self.schedule),
                    fillcolor="rgba(200, 200, 200, 0.2)",
                    line=dict(width=0),
                    layer="below"
                )
            
            current_date += timedelta(days=1)
    
    def _add_holiday_periods(self, blackout_data):
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
                            y1=len(self.schedule),
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
                y1=len(self.schedule),
                fillcolor=fillcolor,
                line=dict(width=0),
                layer="below"
            )
            
            current_day = end_day
            band_count += 1
    
    def _add_dependency_arrows(self):
        """Add dependency arrows between submissions."""
        submissions_dict = self.config.submissions_dict
        sorted_schedule = list(enumerate(sorted(self.schedule.items(), key=lambda x: x[1])))
        
        arrow_count = 0
        max_arrows = 20  # Limit arrows to avoid performance issues
        
        for submission_id, start_date in self.schedule.items():
            if arrow_count >= max_arrows:
                break
                
            submission = submissions_dict.get(submission_id)
            if not submission or not submission.depends_on:
                continue
            
            # Find the row index for this submission
            current_row = None
            for i, (sid, _) in sorted_schedule:
                if sid == submission_id:
                    current_row = i
                    break
            
            if current_row is None:
                continue
            
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
                        
                        # Find the row index for the dependency
                        dep_row = None
                        for i, (sid, _) in sorted_schedule:
                            if sid == dep_id:
                                dep_row = i
                                break
                        
                        if dep_row is not None:
                            self.fig.add_annotation(
                                x=dep_end_days,
                                y=dep_row,
                                xref="x",
                                yref="y",
                                axref="x",
                                ayref="y",
                                ax=current_start_days,
                                ay=current_row,
                                arrowhead=2,
                                arrowsize=1,
                                arrowwidth=2,
                                arrowcolor="gray"
                            )
                            arrow_count += 1
    
    def _configure_layout(self):
        """Configure the chart layout with single x-axis and year annotations."""
        # Primary x-axis (quarters) - on bottom
        primary_axis_config = self.gantt_formatter.get_axis_config()
        
        # Get year annotations to place below the axis
        year_annotations = self.gantt_formatter.get_year_annotations()
        
        # Create y-axis labels for submissions
        sorted_schedule = sorted(self.schedule.items(), key=lambda x: x[1])
        y_labels = []
        for submission_id, _ in sorted_schedule:
            submission = self.config.submissions_dict.get(submission_id)
            if submission:
                display_title = self._get_display_title(submission, submission_id)
                y_labels.append(display_title)
        
        # Update layout with single x-axis and year annotations
        self.fig.update_layout(
            title={
                'text': 'Paper Submission Timeline',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            xaxis=primary_axis_config,
            yaxis={
                'title': 'Submissions',
                'showgrid': True,
                'gridcolor': 'lightgray',
                'tickmode': 'array',
                'tickvals': list(range(len(sorted_schedule))),
                'ticktext': y_labels,
                'tickangle': 0,
                'tickfont': {'size': 10},
                'range': [-0.5, len(sorted_schedule) - 0.5]
            },
            margin=self.gantt_formatter.get_margin_config(),
            height=max(600, len(sorted_schedule) * 30),  # Dynamic height
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
        """Get display title for submission."""
        if submission.title and submission.title.strip():
            return submission.title
        
        if submission_id.endswith('-wrk'):
            mod_id = submission_id[:-4]
            return f"Work {mod_id}"
        if submission_id.endswith('-pap'):
            paper_id = submission_id[:-4]
            return f"Paper {paper_id}"
        return submission_id
    
    def _get_submission_color(self, submission: Submission) -> str:
        """Get color for submission."""
        if submission.kind == SubmissionType.PAPER:
            # Papers: Blue for engineering, Purple for medical
            return '#2E86AB' if submission.engineering else '#A23B72'
        # Abstract/Work item
        # Work items: Orange for engineering, Red for medical
        return '#F18F01' if submission.engineering else '#C73E1D'
    
    def _get_conference_info(self, submission: Submission) -> str:
        """Get conference information for display."""
        if submission.conference_id:
            conference = self.config.conferences_dict.get(submission.conference_id)
            if conference:
                return conference.name
        
        if submission.candidate_conferences:
            # Truncate if too many conferences
            families = submission.candidate_conferences
            if len(families) > 3:
                families = families[:3] + ['...']
            return f"Suggested: {', '.join(families)}"
        
        return "No conference assigned"
    
    def _add_legend(self):
        """Add a legend to explain the color coding."""
        legend_items = [
            ("Engineering Papers", "#2E86AB"),
            ("Medical Papers", "#A23B72"),
            ("Engineering Work", "#F18F01"),
            ("Medical Work", "#C73E1D")
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
