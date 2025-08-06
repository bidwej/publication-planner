"""
Test schedule generation functionality.
"""

import sys
from pathlib import Path
import pytest
from datetime import date

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from core.config import load_config
from core.models import SchedulerStrategy
from schedulers.base import BaseScheduler

# Import schedulers to register them
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler
from schedulers.random import RandomScheduler
from schedulers.heuristic import HeuristicScheduler
from schedulers.optimal import OptimalScheduler

from app.components.charts.gantt_chart import _prepare_gantt_data

def test_schedule_generation():
    """Test that schedule generation works correctly."""
    try:
        print("🔍 Testing schedule generation...")
        
        # Load config
        config = load_config('config.json')
        print(f"✅ Config loaded with {len(config.submissions)} submissions")
        
        # Create scheduler - use the enum value correctly
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, config)
        print("✅ Scheduler created")
        
        # Generate schedule
        schedule = scheduler.schedule()
        print(f"✅ Schedule generated with {len(schedule)} items")
        
        # Show first few items
        print("\n📊 First 5 schedule items:")
        for i, (submission_id, start_date) in enumerate(list(schedule.items())[:5]):
            submission = config.submissions_dict.get(submission_id)
            title = submission.title if submission else "Unknown"
            print(f"  {i+1}. {submission_id} -> {start_date} ({title})")
        
        # Test the Gantt chart data preparation
        gantt_data = _prepare_gantt_data(schedule, config)
        print(f"\n📈 Gantt data prepared:")
        print(f"  - Titles: {len(gantt_data['titles'])}")
        print(f"  - Durations: {len(gantt_data['durations'])}")
        print(f"  - Start days: {len(gantt_data['start_days'])}")
        print(f"  - Colors: {len(gantt_data['colors'])}")
        
        if gantt_data['titles']:
            print(f"\n📝 First 3 titles:")
            for i, title in enumerate(gantt_data['titles'][:3]):
                print(f"  {i+1}. {title}")
        
        print("\n✅ Test completed successfully!")
        
        # Assertions for pytest
        assert len(schedule) > 0, "Schedule should not be empty"
        assert len(gantt_data['titles']) > 0, "Gantt data should have titles"
        assert len(gantt_data['durations']) > 0, "Gantt data should have durations"
        assert len(gantt_data['start_days']) > 0, "Gantt data should have start days"
        assert len(gantt_data['colors']) > 0, "Gantt data should have colors"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    test_schedule_generation()
