#!/usr/bin/env python3
"""Debug script to identify and fix chart visual issues."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Plotly type imports
from plotly.graph_objects import Figure
from plotly.graph_objs import Layout

from app.components.gantt.chart import create_gantt_chart
from app.components.gantt.activity import _get_submission_color, _get_border_color
from src.core.models import Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, Config, ScheduleState, SchedulerStrategy
from datetime import date

def debug_color_logic():
    """Debug the color logic to see what's happening."""
    print("🔍 DEBUGGING COLOR LOGIC:")
    print("="*50)
    
    # Test different submission types
    test_cases = [
        ("Engineering Paper (MOD)", SubmissionType.PAPER, "pccp"),
        ("Medical Paper (ED)", SubmissionType.PAPER, "ed"),
        ("Engineering Abstract", SubmissionType.ABSTRACT, "pccp"),
        ("Medical Abstract", SubmissionType.ABSTRACT, "ed"),
    ]
    
    for desc, kind, author in test_cases:
        submission = Submission(
            id=f"test-{kind.value}-{author}",
            title=f"Test {desc}",
            kind=kind,
            author=author
        )
        
        fill_color = _get_submission_color(submission)
        border_color = _get_border_color(submission)
        
        print(f"\n{desc}:")
        print(f"  Kind: {kind.value}, Author: {author}")
        print(f"  Fill: {fill_color}")
        print(f"  Border: {border_color}")
        print(f"  Different colors: {fill_color != border_color}")

def create_simple_test_data():
    """Create simple test data that should clearly show the distinction."""
    # Create a simple conference
    conference = Conference(
        id="TEST2026",
        name="Test Conference 2026",
        conf_type=ConferenceType.ENGINEERING,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={
            SubmissionType.ABSTRACT: date(2026, 1, 15),
            SubmissionType.PAPER: date(2026, 2, 15)
        }
    )
    
    # Create submissions with clear distinction
    submissions = [
        # Engineering Paper (MOD) - should be BLUE
        Submission(
            id="eng-paper",
            title="Engineering Paper (BLUE)",
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
            author="pccp"
        ),
        # Medical Paper (ED) - should be PURPLE  
        Submission(
            id="med-paper",
            title="Medical Paper (PURPLE)",
            kind=SubmissionType.PAPER,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
            author="ed"
        ),
        # Engineering Abstract - should be ORANGE
        Submission(
            id="eng-abstract",
            title="Engineering Abstract (ORANGE)",
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
            author="pccp"
        ),
        # Medical Abstract - should be ORANGE
        Submission(
            id="med-abstract",
            title="Medical Abstract (ORANGE)",
            kind=SubmissionType.ABSTRACT,
            conference_id="TEST2026",
            depends_on=[],
            draft_window_months=0,
            author="ed"
        )
    ]
    
    # Create config
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
    
    # Create simple schedule - one submission per row
    schedule_state = ScheduleState(
        schedule={
            "eng-paper": date(2024, 12, 1),      # Row 0
            "med-paper": date(2024, 12, 15),     # Row 1  
            "eng-abstract": date(2025, 1, 1),    # Row 2
            "med-abstract": date(2025, 1, 15),   # Row 3
        },
        config=config,
        strategy=SchedulerStrategy.GREEDY,
        metadata={"scheduler": "greedy", "timestamp": "2024-01-01T00:00:00"},
        timestamp="2024-01-01T00:00:00"
    )
    
    return schedule_state

def main():
    """Debug the chart generation issues."""
    print("🚨 DEBUGGING CHART VISUAL ISSUES")
    print("="*60)
    
    # First, debug the color logic
    debug_color_logic()
    
    print("\n" + "="*60)
    print("🔧 CREATING SIMPLE TEST CHART")
    print("="*60)
    
    # Create simple test data
    schedule_state = create_simple_test_data()
    
    print("Test data created:")
    for submission in schedule_state.config.submissions:
        print(f"  {submission.id}: {submission.title} (Author: {submission.author}, Type: {submission.kind.value})")
    
    print("\nGenerating chart...")
    fig = create_gantt_chart(schedule_state)
    
    # Save for inspection
    html_file = "debug_chart.html"
    fig.write_html(html_file)
    print(f"\nChart saved to: {html_file}")
    
    # Analyze what was actually generated
    print("\n" + "="*60)
    print("📊 CHART ANALYSIS")
    print("="*60)
    
    print(f"Title: {fig.layout.title.text}")
    print(f"Shapes (activity bars): {len(fig.layout.shapes)}")
    print(f"Traces (arrows): {len(fig.data)}")
    print(f"Annotations (labels): {len(fig.layout.annotations)}")
    
    # Check activity bars
    if fig.layout.shapes:
        print("\nActivity Bars:")
        for i, shape in enumerate(fig.layout.shapes):
            if shape.type == 'rect' and shape.fillcolor and shape.fillcolor != 'rgba(236, 240, 241, 0.3)':
                print(f"  Bar {i+1}: {shape.fillcolor} at y={shape.y0}-{shape.y1}")
    
    # Check traces
    if fig.data:
        print("\nDependency Arrows:")
        for i, trace in enumerate(fig.data):
            print(f"  Arrow {i+1}: {trace.type}, color={trace.line.color}")
    
    print("\n" + "="*60)
    print("🎯 EXPECTED VS ACTUAL:")
    print("="*60)
    print("EXPECTED:")
    print("  Row 0: Engineering Paper (BLUE)")
    print("  Row 1: Medical Paper (PURPLE)")  
    print("  Row 2: Engineering Abstract (ORANGE)")
    print("  Row 3: Medical Abstract (ORANGE)")
    print("\nCheck the HTML file to see what actually rendered!")
    
    return html_file

if __name__ == "__main__":
    main()
