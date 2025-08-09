#!/usr/bin/env python3
"""
Comprehensive timeline test script to generate multiple screenshots and check for issues.
"""

import asyncio
import time
from pathlib import Path
from tests.common.headless_browser import capture_timeline_screenshots
from src.planner import Planner
from app.components.charts.gantt_chart import generate_gantt_png
from src.core.config import load_config

def test_direct_png_generation():
    """Test direct PNG generation from gantt chart component."""
    print("🔍 Testing direct PNG generation...")
    
    try:
        # Load config and generate schedule
        config = load_config('config.json')
        planner = Planner('config.json')
        schedule = planner.schedule()
        
        print(f"✅ Generated schedule with {len(schedule)} submissions")
        
        # Generate multiple PNGs with different names
        for i in range(3):
            png_filename = f"direct_timeline_{i+1}.png"
            result = generate_gantt_png(schedule, config, png_filename)
            
            if result:
                print(f"✅ Direct PNG #{i+1} generated: {result}")
            else:
                print(f"❌ Direct PNG #{i+1} failed")
                
    except Exception as e:
        print(f"❌ Error in direct PNG generation: {e}")

def test_web_screenshot_generation():
    """Test web screenshot generation."""
    print("\n🔍 Testing web screenshot generation...")
    
    # Generate multiple screenshots to check for consistency
    for i in range(3):
        print(f"\n📸 Generating web screenshot #{i+1}...")
        
        try:
            result = asyncio.run(capture_timeline_screenshots())
            if result:
                print(f"✅ Web screenshot #{i+1} generated successfully")
            else:
                print(f"❌ Web screenshot #{i+1} failed")
        except Exception as e:
            print(f"❌ Error generating web screenshot #{i+1}: {e}")
        
        # Wait a bit between screenshots
        time.sleep(2)

def check_generated_files():
    """Check all generated PNG files."""
    print("\n📁 Checking generated files...")
    
    # Check direct PNG files
    direct_png_files = list(Path(".").glob("direct_timeline*.png"))
    print(f"Direct PNG files: {len(direct_png_files)}")
    for png_file in direct_png_files:
        print(f"  - {png_file.name} ({png_file.stat().st_size} bytes)")
    
    # Check web PNG files
    web_png_files = list(Path(".").glob("web_timeline*.png"))
    print(f"Web PNG files: {len(web_png_files)}")
    for png_file in web_png_files:
        print(f"  - {png_file.name} ({png_file.stat().st_size} bytes)")
    
    # Check dashboard PNG files
    dashboard_png_files = list(Path(".").glob("web_dashboard*.png"))
    print(f"Dashboard PNG files: {len(dashboard_png_files)}")
    for png_file in dashboard_png_files:
        print(f"  - {png_file.name} ({png_file.stat().st_size} bytes)")

def main():
    """Run comprehensive timeline tests."""
    print("🚀 Starting comprehensive timeline test...")
    
    # Test direct PNG generation
    test_direct_png_generation()
    
    # Test web screenshot generation
    test_web_screenshot_generation()
    
    # Check all generated files
    check_generated_files()
    
    print("\n🎯 Comprehensive timeline test completed!")

if __name__ == "__main__":
    main()
