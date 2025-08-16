"""
Dashboard chart generation for Paper Planner.
"""

from datetime import datetime
import plotly.graph_objects as go


def generate_timeline_chart():
    """Generate the timeline chart directly using greedy scheduler."""
    try:
        print("Generating real Paper Planner chart with greedy scheduler...")
        
        # Import real Paper Planner components
        from src.core.config import load_config
        from src.schedulers.greedy import GreedyScheduler
        from app.components.gantt.chart import create_gantt_chart
        
        # Load demo configuration
        config = load_config('app/assets/demo/data/config.json')
        print("✅ Configuration loaded")
        
        # Create greedy scheduler
        scheduler = GreedyScheduler(config)
        
        # Generate real schedule
        schedule = scheduler.schedule()
        
        if schedule:
            print(f"✅ Schedule generated with {len(schedule)} items")
            
            # Create ScheduleState for the chart
            from src.core.models import ScheduleState, SchedulerStrategy
            schedule_state = ScheduleState(
                schedule=schedule,
                config=config,
                strategy=SchedulerStrategy.GREEDY,
                timestamp=datetime.now().isoformat()
            )
            
            # Generate real gantt chart
            fig = create_gantt_chart(schedule_state)
            return fig
        else:
            print("⚠️ No schedule generated")
            return _create_error_chart("No schedule could be generated")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return _create_error_chart(f"Import error: {e}")
    except Exception as e:
        print(f"❌ Error generating chart: {e}")
        return _create_error_chart(f"Error: {e}")


def _create_error_chart(error_msg: str) -> go.Figure:
    """Create an error chart when something goes wrong."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_msg}<br>Check console for details",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(
        title="Paper Planner Timeline - Error",
        xaxis_title="Date",
        yaxis_title="Items",
        height=400
    )
    return fig
