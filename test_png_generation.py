#!/usr/bin/env python3
"""
Test script to generate PNG files with the previous naming convention.
"""

import sys
import os
from datetime import date, timedelta

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.models import Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence
from app.components.charts.gantt_chart import generate_gantt_png

def test_png_generation():
    """Test PNG generation with the previous naming convention."""
    
    # Create a simple test config
    conference = Conference(
        id="TEST2025",
        name="Test Conference 2025",
        conf_type=ConferenceType.ENGINEERING,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={
            SubmissionType.ABSTRACT: date(2025, 3, 1),
            SubmissionType.PAPER: date(2025, 4, 1)
        }
    )
    
    submission = Submission(
        id="test-pap",
        title="Test Paper",
        kind=SubmissionType.PAPER,
        conference_id="TEST2025",
        depends_on=[],
        draft_window_months=3,
        engineering=True
    )
    
    config = Config(
        submissions=[submission],
        conferences=[conference],
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        default_paper_lead_time_months=3,
        penalty_costs={"default_mod_penalty_per_day": 1000},
        priority_weights={
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5,
        },
        scheduling_options={"enable_blackout_periods": True},
        blackout_dates=[],
        data_files={
            "conferences": "conferences.json",
            "papers": "papers.json",
            "mods": "mods.json",
            "blackouts": "data/blackout.json"
        }
    )
    
    # Create a test schedule
    schedule = {
        "test-pap": date(2025, 1, 15)  # This should show weekends and holidays
    }
    
    try:
        # Generate PNG with the previous naming convention
        print("Generating chart_current.png...")
        result1 = generate_gantt_png(schedule, config, "chart_current.png")
        
        print("Generating chart_inspection.png...")
        result2 = generate_gantt_png(schedule, config, "chart_inspection.png")
        
        if result1 and result2:
            print("✅ Both PNG files generated successfully!")
            print(f"📁 Files created: {result1}, {result2}")
            return True
        else:
            print("❌ Failed to generate PNG files")
            return False
            
    except Exception as e:
        print(f"❌ Error generating PNG files: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PNG generation with previous naming convention...")
    success = test_png_generation()
    if success:
        print("\n🎉 PNG generation test passed!")
    else:
        print("\n💥 PNG generation test failed!")
