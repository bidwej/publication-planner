"""
Interactive Gantt chart component for schedule visualization.
"""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, List
import json

from src.core.models import Config, Submission, SubmissionType
from .gantt_formatter import GanttFormatter

class GanttChartBuilder:
    """Builder class for creating Gantt charts with proper separation of concerns."""
    
    def __init__(self, schedule: Dict[str, date], config: Config):
        self.schedule = schedule
        self.config = config
        self.min_date = min(schedule.values()) if schedule else date.today()
        self.max_date = max(schedule.values()) + timedelta(days=90) if schedule else date.today()
        self.fig = go.Figure()
        
        # Initialize Gantt formatter
        self.gantt_formatter = GanttFormatter(self.min_date, self.max_date)
    
    def build(self) -> go.Figure:
        """Build the complete Gantt chart."""
        if not self.schedule:
            return self._create_empty_chart()
        
        self._add_main_bars()
        self._add_blackout_periods()
        self._add_dependency_arrows()
        self._configure_layout()
        
        return self.fig
    
    def _add_main_bars(self):
        """Add the main submission bars."""
        gantt_data = self._prepare_submission_data()
        
        self.fig.add_trace(go.Bar(
            x=gantt_data['durations'],
            y=gantt_data['titles'],
            orientation='h',
            marker=dict(color=gantt_data['colors']),
            text=gantt_data['hover_texts'],
            hoverinfo='text',
            base=gantt_data['start_days']
        ))
    
    def _add_blackout_periods(self):
        """Add blackout period backgrounds including weekends, holidays, and custom periods."""
        blackout_data = self._load_blackout_data()
        
        # Add custom blackout periods
        for period in blackout_data.get('custom_blackout_periods', []):
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
                    y1=1,
                    yref="paper",
                    fillcolor="rgba(128, 128, 128, 0.3)",
                    line=dict(width=0),
                    layer="below"
                )
        
        # Add weekends (recurring)
        if blackout_data.get('weekends', {}).get('enabled', False):
            self._add_weekend_periods()
        
        # Add federal holidays (recurring)
        self._add_holiday_periods(blackout_data)
    
    def _add_weekend_periods(self):
        """Add weekend periods as recurring shaded rectangles."""
        current_date = self.min_date
        while current_date <= self.max_date:
            # Check if it's Saturday or Sunday
            if current_date.weekday() in [5, 6]:  # Saturday=5, Sunday=6
                # Create a 1-day shaded rectangle for this weekend day
                day_offset = (current_date - self.min_date).days
                
                self.fig.add_shape(
                    type="rect",
                    x0=day_offset,
                    x1=day_offset + 1,
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor="rgba(200, 200, 200, 0.2)",
                    line=dict(width=0),
                    layer="below"
                )
            
            current_date += timedelta(days=1)
    
    def _add_holiday_periods(self, blackout_data):
        """Add federal holiday periods as recurring shaded rectangles."""
        # Get all unique holiday dates (without year)
        holiday_dates = set()
        
        for year in ['2025', '2026']:
            holidays = blackout_data.get(f'federal_holidays_{year}', [])
            for holiday_str in holidays:
                holiday_date = date.fromisoformat(holiday_str)
                # Store as month-day for recurring pattern
                holiday_dates.add((holiday_date.month, holiday_date.day))
        
        # Add holiday rectangles for each year in the timeline
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
                            y1=1,
                            yref="paper",
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            line=dict(width=0),
                            layer="below"
                        )
                except ValueError:
                    # Skip invalid dates (like Feb 29 in non-leap years)
                    continue
    

    
    def _add_dependency_arrows(self):
        """Add dependency arrows between submissions."""
        submissions_dict = self.config.submissions_dict
        
        for submission_id, start_date in self.schedule.items():
            submission = submissions_dict.get(submission_id)
            if not submission or not submission.depends_on:
                continue
            
            for dep_id in submission.depends_on:
                if dep_id in self.schedule:
                    dep_start = self.schedule[dep_id]
                    dep_submission = submissions_dict.get(dep_id)
                    if dep_submission:
                        dep_duration = dep_submission.get_duration_days(self.config)
                        dep_end_days = (dep_start + timedelta(days=dep_duration) - self.min_date).days
                        current_start_days = (start_date - self.min_date).days
                        
                        dep_display_title = self._get_display_title(dep_submission, dep_id)
                        current_display_title = self._get_display_title(submission, submission_id)
                        
                        self.fig.add_annotation(
                            x=dep_end_days,
                            y=dep_display_title,
                            xref="x",
                            yref="y",
                            axref="x",
                            ayref="y",
                            ax=current_start_days,
                            ay=current_display_title,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor="gray"
                        )
    
    def _configure_layout(self):
        """Configure the chart layout and axes using Gantt formatter."""
        axis_config = self.gantt_formatter.get_axis_config()
        margin_config = self.gantt_formatter.get_margin_config()
        
        self.fig.update_layout(
            title={'text': 'Schedule Timeline', 'x': 0.5, 'xanchor': 'center'},
            xaxis=axis_config,
            yaxis=dict(title='Papers & Submissions', showgrid=False),
            barmode='overlay',
            height=600,
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=margin_config
        )
    
    def _prepare_submission_data(self) -> Dict[str, List]:
        """Prepare data for submission bars."""
        submissions_dict = self.config.submissions_dict
        
        titles = []
        durations = []
        start_days = []
        colors = []
        hover_texts = []
        
        for submission_id, start_date in self.schedule.items():
            submission = submissions_dict.get(submission_id)
            if not submission:
                continue
            
            duration_days = submission.get_duration_days(self.config)
            start_day = (start_date - self.min_date).days
            
            display_title = self._get_display_title(submission, submission_id)
            hover_text = self._create_hover_text(submission, start_date, duration_days)
            
            titles.append(display_title)
            durations.append(duration_days)
            start_days.append(start_day)
            colors.append(self._get_submission_color(submission))
            hover_texts.append(hover_text)
        
        return {
            'titles': titles,
            'durations': durations,
            'start_days': start_days,
            'colors': colors,
            'hover_texts': hover_texts
        }
    
    def _get_display_title(self, submission: Submission, submission_id: str) -> str:
        """Get display title for submission."""
        if submission.title and submission.title.strip():
            return submission.title
        
        if submission_id.endswith('-wrk'):
            mod_id = submission_id[:-4]
            return f"Work {mod_id}"
        elif submission_id.endswith('-pap'):
            paper_id = submission_id[:-4]
            return f"Paper {paper_id}"
        else:
            return submission_id
    
    def _create_hover_text(self, submission: Submission, start_date: date, duration_days: int) -> str:
        """Create hover text for submission."""
        conference_name = "No conference"
        if submission.conference_id:
            conference = self.config.conferences_dict.get(submission.conference_id)
            if conference:
                conference_name = conference.name
        
        return (f"<b>{submission.title}</b><br>"
                f"Type: {submission.kind.value}<br>"
                f"Conference: {conference_name}<br>"
                f"Start: {start_date.strftime('%Y-%m-%d')}<br>"
                f"Duration: {duration_days} days")
    
    def _get_submission_color(self, submission: Submission) -> str:
        """Get color for submission."""
        if submission.kind == SubmissionType.PAPER:
            return '#2E86AB' if submission.engineering else '#A23B72'
        else:  # Abstract
            return '#F18F01' if submission.engineering else '#C73E1D'
    
    def _load_blackout_data(self) -> Dict:
        """Load blackout data from file."""
        try:
            with open('data/blackout.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load blackout data: {e}")
            return {}
    
    def _create_empty_chart(self) -> go.Figure:
        """Create an empty chart."""
        fig = go.Figure()
        fig.update_layout(
            title={'text': 'No Schedule Available', 'x': 0.5, 'xanchor': 'center'},
            xaxis=dict(title='Timeline (Weeks)'),
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
        
        print(f"✅ Gantt chart saved as {filename}")
        return filename
    except ImportError as e:
        print(f"❌ Missing dependency for PNG generation: {e}")
        print("💡 Install kaleido: pip install kaleido")
        return ""
    except Exception as e:
        print(f"❌ Error generating PNG: {e}")
        return ""

def _prepare_gantt_data(schedule: Dict[str, date], config: Config) -> Dict[str, List]:
    """Prepare data for Gantt chart visualization."""
    builder = GanttChartBuilder(schedule, config)
    return builder._prepare_submission_data()
