#!/usr/bin/env python3
"""
Test script to generate PNG directly from gantt chart component.
"""

from src.planner import Planner
from app.components.charts.gantt_chart import generate_gantt_png
from src.core.config import load_config

def main():
    """Generate PNG directly from gantt chart component."""
    print("🔍 Testing direct PNG generation...")
    
    try:
        # Load config and generate schedule
        config = load_config('config.json')
        planner = Planner('config.json')
        schedule = planner.schedule()
        
        print(f"✅ Generated schedule with {len(schedule)} submissions")
        
        # Generate PNG directly
        png_filename = "direct_timeline.png"
        result = generate_gantt_png(schedule, config, png_filename)
        
        if result:
            print(f"✅ Direct PNG generation successful: {result}")
        else:
            print("❌ Direct PNG generation failed")
            
    except Exception as e:
        print(f"❌ Error in direct PNG generation: {e}")
    
    print("🎯 Direct PNG test completed!")

if __name__ == "__main__":
    main()
