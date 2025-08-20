"""
Sample data generation for Gantt chart demonstrations.
Contains realistic demo data showing proper submission structure and dependencies.
"""

import plotly.graph_objects as go
from plotly.graph_objs import Figure
from datetime import date, timedelta
from typing import Dict, Any, List


def create_sample_gantt_chart() -> Figure:
    """Create a realistic demo gantt chart showing proper submission structure."""
    fig = go.Figure()
    
    # Get sample data
    demo_schedule = _get_sample_schedule()
    submission_details = _get_sample_submission_details()
    activity_rows = _get_sample_activity_rows()
    
    # Add activity bars
    for submission_id, start_date in demo_schedule.items():
        details = submission_details[submission_id]
        duration = details["duration"]
        end_date = start_date + timedelta(days=duration)
        row = activity_rows[submission_id]
        
        # Determine color based on type
        color = _get_submission_type_color(details["type"])
        
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
            x=start_date + timedelta(days=duration // 2),
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
    _add_sample_dependencies(fig, demo_schedule, activity_rows)
    
    # Temporarily comment out today reference line to avoid Plotly compatibility issues
    # _add_today_reference_line(fig)
    
    # Configure layout
    fig.update_layout(
        title='Paper Planner Demo - Real Submission Structure',
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


def create_demo_schedule_from_config(config) -> Dict[str, date]:
    """Create a demo schedule from actual config data."""
    if not config or not hasattr(config, 'submissions') or not config.submissions:
        return {}
    
    demo_schedule = {}
    current_date = date.today()
    
    try:
        for i, submission in enumerate(config.submissions):
            # Ensure submission.id is a string and handle any type issues
            submission_id = str(getattr(submission, 'id', f'submission_{i}'))
            # Space submissions out by 2 weeks each
            start_date = current_date + timedelta(weeks=i * 2)
            demo_schedule[submission_id] = start_date
    except Exception as e:
        print(f"Warning: Could not create demo schedule from config: {e}")
        # Fall back to sample data
        return _get_sample_schedule()
    
    return demo_schedule


def _get_sample_schedule() -> Dict[str, date]:
    """Get sample schedule data showing realistic submission timeline."""
    # Realistic demo data showing the actual rules
    # This demonstrates: abstract+paper as one interval, concurrency on new lines
    return {
        "mod_1": date(2024, 1, 1),      # Work item starts Jan 1
        "mod_2": date(2024, 2, 1),      # Work item starts Feb 1 (concurrent with mod_1)
        "J1-abs": date(2024, 3, 1),     # Abstract for J1 starts Mar 1
        "J1-pap": date(2024, 4, 15),    # Paper for J1 starts Apr 15 (after abstract)
        "J2-abs": date(2024, 3, 15),    # Abstract for J2 starts Mar 15 (concurrent with J1-abs)
        "J2-pap": date(2024, 5, 1),     # Paper for J2 starts May 1 (after abstract)
        "J3": date(2024, 6, 1),         # Direct paper submission starts Jun 1
    }


def _get_sample_submission_details() -> Dict[str, Dict[str, Any]]:
    """Get sample submission details for proper labeling."""
    return {
        "mod_1": {"title": "Samurai Automated 2D", "type": "work_item", "duration": 60},
        "mod_2": {"title": "SLAM Infrastructure", "type": "work_item", "duration": 90},
        "J1-abs": {"title": "CV Endoscopy Review (Abstract)", "type": "abstract", "duration": 30},
        "J1-pap": {"title": "CV Endoscopy Review (Paper)", "type": "paper", "duration": 45},
        "J2-abs": {"title": "Laterality Classifier (Abstract)", "type": "abstract", "duration": 30},
        "J2-pap": {"title": "Laterality Classifier (Paper)", "type": "paper", "duration": 45},
        "J3": {"title": "Polyp Detection", "type": "paper", "duration": 60},
    }


def _get_sample_activity_rows() -> Dict[str, int]:
    """Get sample activity row assignments based on concurrency."""
    # Assign rows based on concurrency (overlapping intervals go on new lines)
    return {
        "mod_1": 0,      # Row 0
        "mod_2": 1,      # Row 1 (concurrent with mod_1)
        "J1-abs": 2,     # Row 2 (starts after mod_1, concurrent with mod_2)
        "J1-pap": 2,     # Row 2 (same row as J1-abs - abstract+paper as one interval)
        "J2-abs": 3,     # Row 3 (concurrent with J1-abs)
        "J2-pap": 3,     # Row 3 (same row as J2-abs - abstract+paper as one interval)
        "J3": 4,         # Row 4 (starts after J1-pap and J2-pap)
    }


def _get_submission_type_color(submission_type: str) -> str:
    """Get color for submission type."""
    color_map = {
        "work_item": "lightblue",
        "abstract": "lightgreen", 
        "paper": "orange",
        "poster": "lightcoral"
    }
    return color_map.get(submission_type, "gray")


def _add_sample_dependencies(fig: Figure, schedule: Dict[str, date], activity_rows: Dict[str, int]) -> None:
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


def _add_today_reference_line(fig: Figure) -> None:
    """Add today's date as reference line."""
    today = date.today()
    fig.add_vline(
        x=today,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text="Today",
        annotation_position="top right"
    )
