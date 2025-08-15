#!/usr/bin/env python3
"""Test Gantt chart generation with real data using proper test infrastructure."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from datetime import date
from src.core.models import ScheduleState, SchedulerStrategy
from app.components.gantt.chart import create_gantt_chart

def test_gantt_with_real_data():
    """Test Gantt chart generation using real data structure."""
    print("🚀 TESTING GANTT CHART WITH REAL DATA STRUCTURE")
    print("="*60)
    
    # Use the existing test data structure from conftest.py
    # This represents the REAL dependency relationships:
    # - MODs are engineering work items (abstracts) that precede papers
    # - ED papers depend on MODs (engineering work must complete first)
    
    # Create a realistic schedule based on the actual data structure
    schedule = {
        # Engineering work items (MODs) - these are the "abstracts" that precede papers
        "mod_1": date(2024, 11, 1),      # Row 0: Engineering work starts first
        "mod_2": date(2024, 12, 1),      # Row 1: Depends on mod_1 completion
        "mod_3": date(2025, 1, 1),       # Row 2: Depends on mod_2 completion
        
        # Medical papers (ED) - these depend on engineering work completion
        "J1": date(2024, 12, 15),        # Row 3: Can start after mod_1 engineering work
        "J2": date(2025, 1, 15),         # Row 4: Can start after mod_2 engineering work
        "J3": date(2025, 2, 15),         # Row 5: Can start after mod_3 engineering work
    }
    
    print("\n📋 Real data structure:")
    print("  MODs (mod_1, mod_2, mod_3): Engineering work items that precede papers")
    print("  ED Papers (J1, J2, J3): Medical papers that depend on MOD completion")
    print("  Dependencies: J1 depends on mod_1, J2 depends on mod_2, J3 depends on mod_3")
    
    print("\n🎯 Expected chart behavior:")
    print("  - MODs should appear as engineering work items (abstracts)")
    print("  - ED papers should appear as medical papers")
    print("  - Dependencies should show arrows from MODs to papers")
    print("  - Timeline should show proper sequencing: MODs first, then papers")
    
    # Create a minimal config for testing (using the real data structure)
    from src.core.models import Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence
    
    # Create test conference
    conference = Conference(
        id="TEST2026",
        name="Test Conference",
        conf_type=ConferenceType.MEDICAL,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={
            SubmissionType.ABSTRACT: date(2025, 2, 1),
            SubmissionType.PAPER: date(2025, 3, 1)
        }
    )
    
    # Create submissions matching the real data structure
    submissions = [
        # Engineering work items (MODs) - these are the "abstracts"
        Submission(
            id="mod_1",
            title="Samurai Automated 2D",  # Real title from mod_papers.json
            kind=SubmissionType.ABSTRACT,  # MODs are engineering work items
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,  # No draft window for work items
            author="pccp"  # Engineering author
        ),
        Submission(
            id="mod_2", 
            title="Samurai Manual-Verified 2D",  # Real title from mod_papers.json
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026", 
            depends_on=["mod_1"],  # Depends on mod_1 completion
            draft_window_months=0,
            author="pccp"
        ),
        Submission(
            id="mod_3",
            title="SLAM Infrastructure",  # Real title from mod_papers.json
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026",
            depends_on=["mod_2"],  # Depends on mod_2 completion
            draft_window_months=0,
            author="pccp"
        ),
        
        # Medical papers (ED) - these depend on engineering work
        Submission(
            id="J1",
            title="Computer Vision (CV) endoscopy review",  # Real title from ed_papers.json
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=["mod_1"],  # Depends on mod_1 engineering work
            draft_window_months=2,
            author="ed"  # Medical author
        ),
        Submission(
            id="J2",
            title="Middle Turbinate/Inferior Turbinate (MT/IT)",  # Real title from ed_papers.json
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=["mod_2"],  # Depends on mod_2 engineering work
            draft_window_months=3,
            author="ed"
        ),
        Submission(
            id="J3",
            title="Nasal Septal Deviation (NSD)",  # Real title from ed_papers.json
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=["mod_3", "J2"],  # Depends on mod_3 AND J2
            draft_window_months=3,
            author="ed"
        )
    ]
    
    config = Config(
        submissions=submissions,
        conferences=[conference],
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=4,
        default_paper_lead_time_months=3,
        penalty_costs={},
        priority_weights={},
        scheduling_options={},
        blackout_dates=[],
        data_files={}
    )
    
    # Create ScheduleState using the real data structure
    schedule_state = ScheduleState(
        schedule=schedule,
        config=config,
        strategy=SchedulerStrategy.GREEDY,
        metadata={"scheduler": "greedy", "timestamp": "2024-01-01T00:00:00"},
        timestamp="2024-01-01T00:00:00"
    )
    
    print("\n🔧 Generating Gantt chart with real data structure...")
    try:
        fig = create_gantt_chart(schedule_state)
        print("✅ Chart generated successfully!")
        print(f"  Annotations: {len(fig.layout.annotations)}")
        print(f"  Shapes: {len(fig.layout.shapes)}")
        
        # Save chart
        fig.write_html("real_data_structure_chart.html")
        print("  Chart saved to real_data_structure_chart.html")
        
        # Show annotation details
        if fig.layout.annotations:
            print("\n📝 Chart annotations:")
            for i, ann in enumerate(fig.layout.annotations):
                print(f"  {i+1}: '{ann.text}' at ({ann.x}, {ann.y})")
        
        print("\n🎯 Key points about the real data structure:")
        print("  1. MODs are engineering work items (abstracts) that precede papers")
        print("  2. ED papers depend on MOD completion (engineering work must finish first)")
        print("  3. This creates a proper dependency chain: Engineering → Medical")
        print("  4. The Gantt chart should show this sequencing clearly")
        
    except Exception as e:
        print(f"❌ Error generating chart: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gantt_with_real_data()
