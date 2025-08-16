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
    # Try to get data from state manager, fall back to sample data
    try:
        from app.storage import get_state_manager
        stored_state = get_state_manager().load_component_state('gantt')
        if stored_state and 'config_data' in stored_state:
            # We have stored config data, use it
            return _create_real_gantt_chart(stored_state['config_data'])
        else:
            return _create_placeholder_gantt_chart()
    except Exception:
        return _create_placeholder_gantt_chart()


def _create_real_gantt_chart(config_data: Dict[str, Any]) -> Figure:
    """Create a gantt chart with real data from stored state."""
    fig = go.Figure()
    
    schedule = config_data.get('schedule', {})
    config = config_data.get('config')
    
    if schedule and config:
        # Create a proper timeline chart
        fig.update_layout(
            title='Paper Planner Timeline',
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


def _create_placeholder_gantt_chart() -> Figure:
    """Create a placeholder gantt chart."""
    fig = go.Figure()
    
    # Sample gantt data
    tasks: List[str] = ['Task A', 'Task B', 'Task C', 'Task D']
    start_dates: List[str] = ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15']
    end_dates: List[str] = ['2024-01-14', '2024-01-31', '2024-02-14', '2024-02-28']
    
    for i, task in enumerate(tasks):
        fig.add_trace(go.Bar(
            name=task,
            x=[(end_dates[i], start_dates[i])],
            y=[task],
            orientation='h',
            marker_color='lightblue',
            opacity=0.8
        ))
    
    fig.update_layout(
        title='Paper Planner Gantt Chart',
        xaxis_title='Timeline',
        yaxis_title='Tasks',
        height=400,
        barmode='overlay',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig


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
