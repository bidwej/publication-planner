#!/usr/bin/env python3
"""
Capture the timeline dashboard as PNG.
"""

import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

def is_timeline_running():
    """Check if the timeline dashboard is running."""
    try:
        response = requests.get('http://127.0.0.1:8051', timeout=2)
        return response.status_code == 200
    except:
        return False

def start_timeline():
    """Start the timeline dashboard in the background."""
    print("🚀 Starting timeline dashboard...")
    try:
        process = subprocess.Popen([
            'python', 'run_web_timeline.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for it to start
        print("⏳ Waiting for timeline to start...")
        for i in range(10):  # Wait up to 10 seconds
            if is_timeline_running():
                print("✅ Timeline is running!")
                return process
            time.sleep(1)
            print(f"   Waiting... ({i+1}/10)")
        
        print("❌ Timeline failed to start within 10 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error starting timeline: {e}")
        return None

async def capture_timeline():
    """Capture the timeline dashboard as PNG."""
    
    # Check if timeline is running, start if not
    if not is_timeline_running():
        print("📊 Timeline not running, starting it...")
        process = start_timeline()
        if not process:
            print("❌ Failed to start timeline. Please run manually:")
            print("   python run_web_timeline.py")
            return
    else:
        print("✅ Timeline is already running!")
        process = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 Capturing timeline...")
        
        try:
            # Navigate to the timeline
            await page.goto('http://127.0.0.1:8051')
            print("✅ Loaded timeline")
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)  # Extra wait for charts
            
            # Take screenshot
            await page.screenshot(path='timeline_dashboard.png', full_page=True)
            print("📸 Screenshot saved as 'timeline_dashboard.png'")
            
            # Inspect chart elements
            print("\n📊 INSPECTING TIMELINE ELEMENTS:")
            
            # Check for shapes (blackout periods)
            shapes = await page.query_selector_all('.shape-group')
            print(f"🔲 Shape groups (blackout periods): {len(shapes)}")
            
            # Check for vlines (holiday lines)
            vlines = await page.query_selector_all('.vline')
            print(f"📏 Vertical lines (holidays): {len(vlines)}")
            
            # Check for bars
            bars = await page.query_selector_all('.trace.bars')
            print(f"📊 Bar traces: {len(bars)}")
            
            print("\n✅ Timeline capture complete!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await browser.close()
            
            # Stop the timeline process if we started it
            if process:
                print("🛑 Stopping timeline...")
                process.terminate()
                process.wait()
                print("✅ Timeline stopped. Exiting.")
            else:
                print("✅ Timeline capture complete. Exiting.")

if __name__ == "__main__":
    asyncio.run(capture_timeline())
