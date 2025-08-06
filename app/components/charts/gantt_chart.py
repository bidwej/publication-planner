"""
Interactive Gantt chart component for schedule visualization.
"""

import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Dict, List, Optional
import json
from core.models import Config, Submission, SubmissionType

class GanttChartBuilder:
    """Builder class for creating Gantt charts with proper separation of concerns."""
    
    def __init__(self, schedule: Dict[str, date], config: Config):
        self.schedule = schedule
        self.config = config
        self.min_date = min(schedule.values()) if schedule else date.today()
        self.max_date = max(schedule.values()) + timedelta(days=90) if schedule else date.today()
        self.fig = go.Figure()
    
    def build(self) -> go.Figure:
        """Build the complete Gantt chart."""
        if not self.schedule:
            return self._create_empty_chart()
        
        self._add_main_bars()
        self._add_blackout_periods()
        self._add_holiday_lines()
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
        """Add blackout period backgrounds."""
        blackout_data = self._load_blackout_data()
        
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
                    fillcolor="rgba(128, 128, 128, 0.4)",
                    line=dict(width=0),
                    layer="below"
                )
    
    def _add_holiday_lines(self):
        """Add federal holiday vertical lines."""
        blackout_data = self._load_blackout_data()
        
        holiday_x = []
        holiday_y = []
        holiday_text = []
        
        for year in ['2025', '2026']:
            holidays = blackout_data.get(f'federal_holidays_{year}', [])
            for holiday_str in holidays:
                holiday_date = date.fromisoformat(holiday_str)
                if self.min_date <= holiday_date <= self.max_date:
                    holiday_days = (holiday_date - self.min_date).days
                    
                    holiday_x.append(holiday_days)
                    holiday_y.append(0.5)  # Middle of chart
                    holiday_text.append(f"Holiday: {holiday_date.strftime('%Y-%m-%d')}")
        
        if holiday_x:
            # Add holiday lines as scatter trace
            self.fig.add_trace(go.Scatter(
                x=holiday_x,
                y=holiday_y,
                mode='markers+text',
                marker=dict(
                    symbol='line-ns',
                    size=20,
                    color='red',
                    line=dict(color='red', width=3)
                ),
                text=holiday_text,
                textposition='top center',
                name='Federal Holidays',
                showlegend=False,
                hoverinfo='text'
            ))
    
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
        """Configure the chart layout and axes."""
        timeline_days = (self.max_date - self.min_date).days
        timeline_weeks = timeline_days // 7 + 1
        
        # Create weekly tick marks with actual dates
        weekly_ticks = []
        weekly_labels = []
        
        for week in range(0, timeline_weeks + 1, 4):  # Show every 4 weeks
            week_start = self.min_date + timedelta(days=week * 7)
            weekly_ticks.append(week * 7)
            # Use proper line break for Plotly
            weekly_labels.append(f"Week {week}<br>{week_start.strftime('%Y-%m-%d')}")
        
        self.fig.update_layout(
            title={'text': 'Schedule Timeline', 'x': 0.5, 'xanchor': 'center'},
            xaxis=dict(
                title='Timeline (Weeks)', 
                showgrid=True, 
                gridcolor='lightgray',
                tickmode='array',
                tickvals=weekly_ticks,
                ticktext=weekly_labels,
                range=[0, timeline_days]
            ),
            yaxis=dict(title='Papers & Submissions', showgrid=False),
            barmode='overlay',
            height=600,
            showlegend=False,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=80, b=50)
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

def _prepare_gantt_data(schedule: Dict[str, date], config: Config) -> Dict[str, List]:
    """Prepare data for Gantt chart visualization."""
    builder = GanttChartBuilder(schedule, config)
    return builder._prepare_submission_data()
