#!/usr/bin/env python3
"""
Generate PNG files using Playwright to take screenshots of the web dashboard.
Uses the previous naming convention: chart_current.png and chart_inspection.png
"""

import asyncio
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright
import time

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import load_config
from core.models import SchedulerStrategy
from schedulers.base import BaseScheduler

async def generate_chart_pngs():
    """Generate PNG files using Playwright screenshots."""
    
    # Load config
    config = load_config('data/config.json')
    
    # Generate a sample schedule
    scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, config)
    schedule = scheduler.schedule()
    
    if not schedule:
        print("❌ No schedule generated")
        return False
    
    print("🚀 Starting web dashboard for screenshot...")
    
    # Start the web dashboard in the background
    import subprocess
    import threading
    
    # Start the web server
    process = subprocess.Popen([
        sys.executable, 'run_web_dashboard.py'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the dashboard
            print("🌐 Navigating to dashboard...")
            await page.goto('http://127.0.0.1:8050')
            
            # Wait for the page to load
            await page.wait_for_load_state('networkidle')
            
            # Wait for charts to render
            print("📊 Waiting for charts to render...")
            await page.wait_for_timeout(3000)  # Wait 3 seconds for charts
            
            # Take screenshot of the main chart area
            print("📸 Taking screenshot of chart_current.png...")
            chart_element = await page.query_selector('#gantt-chart')
            if chart_element:
                await chart_element.screenshot(path='chart_current.png')
                print("✅ chart_current.png generated")
            else:
                # Fallback to full page screenshot
                await page.screenshot(path='chart_current.png')
                print("✅ chart_current.png generated (full page)")
            
            # Take another screenshot for inspection
            print("📸 Taking screenshot of chart_inspection.png...")
            await page.screenshot(path='chart_inspection.png')
            print("✅ chart_inspection.png generated")
            
            await browser.close()
            
    except Exception as e:
        print(f"❌ Error taking screenshots: {e}")
        return False
    finally:
        # Stop the web server
        process.terminate()
        process.wait()
    
    print("🎉 PNG generation completed!")
    return True

def main():
    """Main entry point."""
    print("🖼️  Generating chart PNG files using Playwright...")
    
    # Run the async function
    success = asyncio.run(generate_chart_pngs())
    
    if success:
        print("✅ Successfully generated PNG files!")
        print("📁 Files created:")
        print("   - chart_current.png")
        print("   - chart_inspection.png")
    else:
        print("❌ Failed to generate PNG files")

if __name__ == "__main__":
    main()
