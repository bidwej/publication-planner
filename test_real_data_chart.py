#!/usr/bin/env python3
"""Test chart generation with real data from data files."""

import sys
import os
import json
sys.path.insert(0, os.path.abspath('.'))

from datetime import date
from src.core.models import Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, ScheduleState, SchedulerStrategy
from app.components.gantt.chart import create_gantt_chart

def load_real_data():
    """Load real data from data files."""
    print("📁 Loading real data from data files...")
    
    # Load conferences
    with open('data/conferences.json', 'r') as f:
        conferences_data = json.load(f)
    
    # Load engineering papers (MODs)
    with open('data/mod_papers.json', 'r') as f:
        mod_papers = json.load(f)
    
    # Load medical papers (ED)
    with open('data/ed_papers.json', 'r') as f:
        ed_papers = json.load(f)
    
    print(f"  📊 Loaded {len(conferences_data)} conferences")
    print(f"  🔧 Loaded {len(mod_papers)} engineering papers")
    print(f"  🏥 Loaded {len(ed_papers)} medical papers")
    
    return conferences_data, mod_papers, ed_papers

def create_real_test_data():
    """Create test data using real paper titles."""
    print("\n🔧 Creating test data with real paper titles...")
    
    # Use first conference
    conference = Conference(
        id="TEST2026",
        name="Test Conference",
        conf_type=ConferenceType.ENGINEERING,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={
            SubmissionType.ABSTRACT: date(2025, 2, 1),
            SubmissionType.PAPER: date(2025, 3, 1)
        }
    )
    
    # Create submissions with REAL titles from data files
    submissions = [
        # Engineering Paper (PCCP) - using real title
        Submission(
            id="mod_1",
            title="Samurai Automated 2D",  # REAL title from mod_papers.json
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=2,
            author="pccp"
        ),
        # Medical Paper (ED) - using real title
        Submission(
            id="J1",
            title="Computer Vision (CV) endoscopy review",  # REAL title from ed_papers.json
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=2,
            author="ed"
        ),
        # Engineering Abstract (PCCP)
        Submission(
            id="eng-abstract",
            title="Engineering Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
            author="pccp"
        ),
        # Medical Abstract (ED)
        Submission(
            id="med-abstract",
            title="Medical Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
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
    
    # Create ScheduleState object
    schedule_state = ScheduleState(
        schedule={
            "mod_1": date(2024, 12, 1),      # Row 0: Engineering Paper
            "J1": date(2024, 12, 15),        # Row 1: Medical Paper
            "eng-abstract": date(2025, 1, 1),    # Row 2: Engineering Abstract
            "med-abstract": date(2025, 1, 15),   # Row 3: Medical Abstract
        },
        config=config,
        strategy=SchedulerStrategy.GREEDY,
        metadata={"scheduler": "greedy", "timestamp": "2024-01-01T00:00:00"},
        timestamp="2024-01-01T00:00:00"
    )
    
    return schedule_state

def main():
    """Create a chart with real data."""
    print("🚀 TESTING CHART WITH REAL DATA")
    print("="*60)
    
    # Load real data to show what's available
    load_real_data()
    
    # Create test data with real paper titles
    schedule_state = create_real_test_data()
    
    print("\n📋 Test data created:")
    for submission in schedule_state.config.submissions:
        print(f"  {submission.id}: '{submission.title}' (Author: {submission.author}, Type: {submission.kind.value})")
    
    print("\n🎯 Expected chart labels:")
    print("  Row 0: Type: 'Paper: Engineering' (top-right), Title: 'Samurai Automated 2D' (center)")
    print("  Row 1: Type: 'Paper: Medical' (top-right), Title: 'Computer Vision (CV) endoscopy review' (center)")
    print("  Row 2: Type: 'Abstract: Engineering' (top-left), Title: 'Engineering Abstract' (center)")
    print("  Row 3: Type: 'Abstract: Medical' (top-left), Title: 'Medical Abstract' (center)")
    
    print("\n🔧 Generating chart...")
    try:
        fig = create_gantt_chart(schedule_state)
        print("✅ Chart generated successfully!")
        print(f"Annotations: {len(fig.layout.annotations)}")
        print(f"Shapes: {len(fig.layout.shapes)}")
        
        # Save chart
        fig.write_html("real_data_chart.html")
        print("Chart saved to real_data_chart.html")
        
        # Show annotation details
        if fig.layout.annotations:
            print("\n📝 Annotations found:")
            for i, ann in enumerate(fig.layout.annotations):
                print(f"  {i+1}: '{ann.text}' at ({ann.x}, {ann.y})")
        
    except Exception as e:
        print(f"❌ Error generating chart: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
