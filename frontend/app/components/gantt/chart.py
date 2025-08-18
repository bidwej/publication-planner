"""
Gantt chart component for timeline visualization.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

# Import helper that works in both pytest and direct execution
def _import_backend_modules():
    """Import backend modules with fallback for direct execution."""
    try:
        # Try pytest context first
        from core.models import Config, Submission
        from core.config import load_config
        return Config, Submission, load_config
    except ImportError:
        try:
            # Try direct execution context
            import sys
            from pathlib import Path
            backend_src = Path(__file__).parent.parent.parent.parent / "backend" / "src"
            if backend_src.exists():
                sys.path.insert(0, str(backend_src))
                from core.models import Config, Submission
                from core.config import load_config
                return Config, Submission, load_config
            else:
                return None, None, None
        except ImportError:
            return None, None, None

# Import backend modules
Config, Submission, load_config = _import_backend_modules()


def create_gantt_chart() -> Figure:
    """Create the main gantt chart - public function.
    
    Returns:
        Plotly Figure object
    """
    # Until backend API integration is added, always render placeholder chart
    return _create_placeholder_gantt_chart()


def _create_real_gantt_chart(config_data: Dict[str, Any]) -> Figure:
    """Create a gantt chart with real data from stored state or database."""
    fig = go.Figure()
    
    # Backend data loading is not handled here. Use any provided config_data keys
    # if present; otherwise this will fall back to empty and the caller should
    # decide whether to render a placeholder.
    schedule = config_data.get('schedule', {})
    config = config_data.get('config', {})
    
    if schedule and config:
        # Create a proper timeline chart
        fig.update_layout(
            title='Paper Planner Timeline - Database Data',
            xaxis_title='Timeline',
            yaxis_title='Activities',
            height=600,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=60, r=60, t=80, b=60),
            xaxis=dict(
                type='date',
                showgrid=True,
                gridcolor='lightgray',
                tickformat='%Y-%m-%d'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                showticklabels=True
            )
        )
        
        # Try to use advanced features, fall back to simple if not available
        try:
            from app.components.gantt.activity import add_activity_bars
            from app.components.gantt.timeline import add_background_elements
            
            add_activity_bars(fig, schedule, config)
            add_background_elements(fig)
        except ImportError:
            # Fall back to enhanced simple chart if advanced modules aren't available
            _add_enhanced_activity_bars(fig, schedule, config)
        
        # Set y-axis range based on number of activities
        if schedule:
            num_activities = len(schedule)
            fig.update_layout(yaxis=dict(range=[-0.5, num_activities - 0.5]))
            
    else:
        # No schedule or config data available, show empty chart
        return _create_empty_chart()
    
    return fig


def _add_enhanced_activity_bars(fig: Figure, schedule: Dict[str, Any], config: Any) -> None:
    """Add enhanced activity bars as fallback when advanced functions aren't available."""
    if not schedule:
        return
    
    # Get unique activities for y-axis labels
    activities = list(schedule.keys())
    
    # Try to get submission titles from config if available
    submission_titles = {}
    if config and hasattr(config, 'submissions_dict'):
        for submission_id, submission in config.submissions_dict.items():
            if hasattr(submission, 'title'):
                submission_titles[submission_id] = submission.title
    
    # Add enhanced bars for each activity
    for i, (activity_id, start_date) in enumerate(schedule.items()):
        # Handle different date formats
        if isinstance(start_date, str):
            try:
                start_date = date.fromisoformat(start_date)
            except ValueError:
                continue
        
        # Use a reasonable duration (try to get from config if available)
        duration_days = 7  # Default duration
        if config and hasattr(config, 'submissions_dict'):
            submission = config.submissions_dict.get(activity_id)
            if submission and hasattr(submission, 'get_duration_days'):
                try:
                    duration_days = max(submission.get_duration_days(config), 7)
                except:
                    pass
        
        end_date = start_date + timedelta(days=duration_days)
        
        # Get display name (title if available, otherwise ID)
        display_name = submission_titles.get(activity_id, activity_id)
        
        # Add the bar with better styling
        fig.add_shape(
            type="rect",
            x0=start_date, y0=i - 0.4,
            x1=end_date, y1=i + 0.4,
            fillcolor="lightblue",
            line=dict(color="blue", width=1),
            opacity=0.8,
            layer="below"
        )
        
        # Add activity label with better positioning
        fig.add_annotation(
            text=display_name,
            x=start_date, y=i,
            xanchor='left', yanchor='middle',
            showarrow=False,
            font=dict(size=10, color="black"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgray",
            borderwidth=1
        )
        
        # Add duration label
        duration_text = f"{duration_days} days"
        fig.add_annotation(
            text=duration_text,
            x=end_date, y=i,
            xanchor='right', yanchor='middle',
            showarrow=False,
            font=dict(size=8, color="darkblue"),
            bgcolor="rgba(255,255,255,0.6)"
        )
    
    # Update y-axis with activity labels
    fig.update_layout(
        yaxis=dict(
            ticktext=[submission_titles.get(act, act) for act in activities],
            tickvals=list(range(len(activities))),
            showticklabels=True
        )
    )
    
    # Add today's date as a reference line
    today = date.today()
    fig.add_vline(
        x=today,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text="Today",
        annotation_position="top right"
    )


# Note: Schedule loading is handled by backend, not frontend
# Frontend only manages component state and UI

def _create_placeholder_gantt_chart() -> Figure:
    """Create a realistic demo gantt chart showing proper submission structure."""
    fig = go.Figure()
    
    # Realistic demo data showing the actual rules
    # This demonstrates: abstract+paper as one interval, concurrency on new lines
    demo_schedule = {
        "mod_1": date(2024, 1, 1),      # Work item starts Jan 1
        "mod_2": date(2024, 2, 1),      # Work item starts Feb 1 (concurrent with mod_1)
        "J1-abs": date(2024, 3, 1),     # Abstract for J1 starts Mar 1
        "J1-pap": date(2024, 4, 15),    # Paper for J1 starts Apr 15 (after abstract)
        "J2-abs": date(2024, 3, 15),    # Abstract for J2 starts Mar 15 (concurrent with J1-abs)
        "J2-pap": date(2024, 5, 1),     # Paper for J2 starts May 1 (after abstract)
        "J3": date(2024, 6, 1),         # Direct paper submission starts Jun 1
    }
    
    # Submission details for proper labeling
    submission_details = {
        "mod_1": {"title": "Samurai Automated 2D", "type": "work_item", "duration": 60},
        "mod_2": {"title": "SLAM Infrastructure", "type": "work_item", "duration": 90},
        "J1-abs": {"title": "CV Endoscopy Review (Abstract)", "type": "abstract", "duration": 30},
        "J1-pap": {"title": "CV Endoscopy Review (Paper)", "type": "paper", "duration": 45},
        "J2-abs": {"title": "Laterality Classifier (Abstract)", "type": "abstract", "duration": 30},
        "J2-pap": {"title": "Laterality Classifier (Paper)", "type": "paper", "duration": 45},
        "J3": {"title": "Polyp Detection", "type": "paper", "duration": 60},
    }
    
    # Assign rows based on concurrency (overlapping intervals go on new lines)
    activity_rows = {
        "mod_1": 0,      # Row 0
        "mod_2": 1,      # Row 1 (concurrent with mod_1)
        "J1-abs": 2,     # Row 2 (starts after mod_1, concurrent with mod_2)
        "J1-pap": 2,     # Row 2 (same row as J1-abs - abstract+paper as one interval)
        "J2-abs": 3,     # Row 3 (concurrent with J1-abs)
        "J2-pap": 3,     # Row 3 (same row as J2-abs - abstract+paper as one interval)
        "J3": 4,         # Row 4 (starts after J1-pap and J2-pap)
    }
    
    # Add activity bars
    for submission_id, start_date in demo_schedule.items():
        details = submission_details[submission_id]
        duration = details["duration"]
        end_date = start_date + timedelta(days=duration)
        row = activity_rows[submission_id]
        
        # Determine color based on type
        if details["type"] == "work_item":
            color = "lightblue"
        elif details["type"] == "abstract":
            color = "lightgreen"
        elif details["type"] == "paper":
            color = "orange"
        else:
            color = "gray"
        
        # Add the bar
        fig.add_trace(go.Bar(
            name=details["title"],
            x=[(end_date, start_date)],  # Plotly expects (end, start) for horizontal bars
            y=[f"Row {row}"],
            orientation='h',
            marker_color=color,
            opacity=0.8,
            showlegend=False
        ))
        
        # Add label
        fig.add_annotation(
            text=details["title"][:25] + "..." if len(details["title"]) > 25 else details["title"],
            x=start_date + timedelta(days=duration/2),
            y=row,
            xanchor='center',
            yanchor='middle',
            showarrow=False,
            font=dict(size=10, color="black"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        )
    
    # Add dependency arrows
    _add_demo_dependencies(fig, demo_schedule, activity_rows)
    
    # Add today's date as reference line
    today = date.today()
    fig.add_vline(
        x=today,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text="Today",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title='Paper Planner Demo - Real Submission Structure',
        subtitle='Shows: Abstract+Paper as one interval, Concurrency on new lines',
        xaxis_title='Timeline',
        yaxis_title='Activities',
        height=500,
        barmode='overlay',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=100, b=60),
        xaxis=dict(
            type='date',
            showgrid=True,
            gridcolor='lightgray',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            showticklabels=True,
            ticktext=[f"Row {i}" for i in range(5)],
            tickvals=list(range(5))
        )
    )
    
    return fig


def _add_demo_dependencies(fig: Figure, schedule: Schedule, activity_rows: Dict[str, int]) -> None:
    """Add dependency arrows to the demo chart."""
    # Dependencies: mod_1 → J1-abs, mod_2 → J2-abs, J1-abs → J1-pap, J2-abs → J2-pap
    dependencies = [
        ("mod_1", "J1-abs"),
        ("mod_2", "J2-abs"), 
        ("J1-abs", "J1-pap"),
        ("J2-abs", "J2-pap")
    ]
    
    for dep_id, dependent_id in dependencies:
        if dep_id in schedule and dependent_id in schedule:
            # Calculate end date of dependency
            dep_start = schedule[dep_id]
            dep_end = dep_start + timedelta(days=30)  # Assume 30 days duration
            
            # Draw arrow from end of dependency to start of dependent
            fig.add_annotation(
                x=dep_end,
                y=activity_rows[dep_id],
                ax=schedule[dependent_id],
                ay=activity_rows[dependent_id],
                xref="x",
                yref="y",
                axref="x", 
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="red",
                opacity=0.7
            )


def _create_empty_chart() -> Figure:
    """Create empty chart when no data is available."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available<br>Please load a schedule",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="#666")
    )
    fig.update_layout(
        title="Paper Planner Gantt Chart",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig


def _create_error_chart(error_msg: str) -> Figure:
    """Create an error chart when something goes wrong."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_msg}<br>Check console for details",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color="#e74c3c")
    )
    fig.update_layout(
        title="Paper Planner Gantt - Error",
        xaxis_title="Date",
        yaxis_title="Tasks",
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig
