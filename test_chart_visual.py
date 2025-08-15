#!/usr/bin/env python3
"""Test script to generate and visually inspect gantt charts."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.components.gantt.chart import create_gantt_chart
from src.core.models import Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, Config, ScheduleState, SchedulerStrategy
from datetime import date
import plotly.graph_objects as go

def create_test_data():
    """Create test data for visual inspection."""
    # Create test conferences
    conferences = [
        Conference(
            id="ICRA2026",
            name="IEEE International Conference on Robotics and Automation 2026",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 1, 15),
                SubmissionType.PAPER: date(2026, 2, 15)
            }
        ),
        Conference(
            id="MICCAI2026",
            name="Medical Image Computing and Computer Assisted Intervention 2026",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 3, 1),
                SubmissionType.PAPER: date(2026, 4, 1)
            }
        )
    ]
    
    # Create test submissions with clear engineering vs medical distinction
    submissions = [
        # Engineering papers (MODs) - should be BLUE
        Submission(
            id="mod1-wrk",
            title="Endoscope Navigation Module (Engineering)",
            kind=SubmissionType.ABSTRACT,
            conference_id="ICRA2026",
            depends_on=[],
            draft_window_months=0,
            author="pccp"  # Engineering author
        ),
        Submission(
            id="paper1-pap",
            title="AI-Powered Endoscope Control (Engineering)",
            kind=SubmissionType.PAPER,
            conference_id="ICRA2026",
            depends_on=["mod1-wrk"],
            draft_window_months=3,
            author="pccp"  # Engineering author
        ),
        # Medical papers (ED) - should be PURPLE
        Submission(
            id="mod2-wrk",
            title="Medical Image Analysis Module (Medical)",
            kind=SubmissionType.ABSTRACT,
            conference_id="MICCAI2026",
            depends_on=[],
            draft_window_months=0,
            author="ed"  # Medical author
        ),
        Submission(
            id="paper2-pap",
            title="Deep Learning for Endoscope Guidance (Medical)",
            kind=SubmissionType.PAPER,
            conference_id="MICCAI2026",
            depends_on=["mod2-wrk"],
            draft_window_months=3,
            author="ed"  # Medical author
        )
    ]
    
    # Create config
    config = Config(
        submissions=submissions,
        conferences=conferences,
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        default_paper_lead_time_months=3,
        penalty_costs={},
        priority_weights={},
        scheduling_options={},
        blackout_dates=[],
        data_files={}
    )
    
    # Create schedule state
    schedule_state = ScheduleState(
        schedule={
            "mod1-wrk": date(2024, 12, 1),
            "paper1-pap": date(2025, 1, 15),
            "mod2-wrk": date(2025, 1, 1),
            "paper2-pap": date(2025, 2, 1)
        },
        config=config,
        strategy=SchedulerStrategy.GREEDY,
        metadata={
            "scheduler": "greedy",
            "timestamp": "2024-01-01T00:00:00"
        },
        timestamp="2024-01-01T00:00:00"
    )
    
    return schedule_state

def main():
    """Generate and save gantt chart for visual inspection."""
    print("Creating test data...")
    schedule_state = create_test_data()
    
    print("Generating gantt chart...")
    fig = create_gantt_chart(schedule_state)
    
    # Save as HTML for interactive inspection
    html_file = "gantt_chart_visual_test.html"
    fig.write_html(html_file)
    print(f"HTML chart saved to: {html_file}")
    
    # Save as PNG for static visual inspection
    png_file = "gantt_chart_visual_test.png"
    fig.write_image(png_file, width=1200, height=800)
    print(f"PNG chart saved to: {png_file}")
    
    # Print chart details for manual verification
    print("\n" + "="*60)
    print("CHART VISUAL INSPECTION DETAILS")
    print("="*60)
    
    print(f"Title: {fig.layout.title.text}")
    print(f"Dimensions: {fig.layout.width} x {fig.layout.height}")
    print(f"Background: plot_bgcolor={fig.layout.plot_bgcolor}, paper_bgcolor={fig.layout.paper_bgcolor}")
    
    # Check activity bars (shapes)
    if fig.layout.shapes:
        print(f"\nActivity Bars (Shapes): {len(fig.layout.shapes)}")
        for i, shape in enumerate(fig.layout.shapes):
            print(f"  Bar {i+1}: type={shape.type}, fillcolor={shape.fillcolor}, border_color={shape.line.color}")
            print(f"    Position: x0={shape.x0}, x1={shape.x1}, y0={shape.y0}, y1={shape.y1}")
            print(f"    Style: opacity={shape.opacity}, line_width={shape.line.width}")
    else:
        print("\nNo activity bars found!")
    
    # Check dependency arrows (traces)
    if fig.data:
        print(f"\nDependency Arrows (Traces): {len(fig.data)}")
        for i, trace in enumerate(fig.data):
            print(f"  Arrow {i+1}: type={trace.type}, color={trace.line.color}")
            print(f"    Style: width={trace.line.width}, dash={trace.line.dash}")
    else:
        print("\nNo dependency arrows found!")
    
    # Check annotations (labels)
    if fig.layout.annotations:
        print(f"\nLabels (Annotations): {len(fig.layout.annotations)}")
        for i, annotation in enumerate(fig.layout.annotations):
            print(f"  Label {i+1}: text='{annotation.text}', x={annotation.x}, y={annotation.y}")
    else:
        print("\nNo labels found!")
    
    print("\n" + "="*60)
    print("MANUAL VERIFICATION CHECKLIST:")
    print("="*60)
    print("1. Open the HTML file in a browser to see the interactive chart")
    print("2. Check the PNG file for static visual inspection")
    print("3. Verify engineering papers (MODs) are BLUE")
    print("4. Verify medical papers (ED) are PURPLE")
    print("5. Verify NO double border effect (fill ≠ border colors)")
    print("6. Verify background rendering is correct")
    print("7. Verify activity bars are positioned correctly")
    print("8. Verify dependency arrows connect properly")
    
    return html_file, png_file

if __name__ == "__main__":
    main()
