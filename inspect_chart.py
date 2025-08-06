#!/usr/bin/env python3
"""
Inspect the chart and generate PNG to see what's wrong.
"""

import sys
import os
import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

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

def is_dashboard_running():
    """Check if the web dashboard is running."""
    try:
        response = requests.get('http://127.0.0.1:8050', timeout=2)
        return response.status_code == 200
    except:
        return False

def start_dashboard():
    """Start the web dashboard in the background."""
    print("🚀 Starting web dashboard...")
    try:
        # Start the dashboard process
        process = subprocess.Popen([
            sys.executable, 'run_web_dashboard.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for it to start
        print("⏳ Waiting for dashboard to start...")
        for i in range(30):  # Wait up to 30 seconds
            if is_dashboard_running():
                print("✅ Dashboard is running!")
                return process
            time.sleep(1)
            print(f"   Waiting... ({i+1}/30)")
        
        print("❌ Dashboard failed to start within 30 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return None

async def inspect_chart():
    """Inspect the chart and generate PNG."""
    
    # Check if dashboard is running, start if not
    if not is_dashboard_running():
        print("📊 Dashboard not running, starting it...")
        process = start_dashboard()
        if not process:
            print("❌ Failed to start dashboard. Please run manually:")
            print("   python run_web_dashboard.py")
            return
    else:
        print("✅ Dashboard is already running!")
        process = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Changed to False for debugging
        page = await browser.new_page()
        
        print("🔍 Inspecting chart...")
        
        try:
            # Navigate to the app
            await page.goto('http://127.0.0.1:8050')
            print("✅ Loaded app")
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            
            # Wait for generate button
            await page.wait_for_selector('#generate-btn', timeout=10000)
            print("✅ Found generate button")
            
            # Click generate
            await page.click('#generate-btn')
            print("✅ Clicked generate")
            
            # Wait for chart
            await page.wait_for_timeout(3000)
            
            # Take screenshot
            await page.screenshot(path='chart_current.png', full_page=True)
            print("📸 Screenshot saved as 'chart_current.png'")
            
            # Take another screenshot for inspection
            await page.screenshot(path='chart_inspection.png', full_page=True)
            print("📸 Screenshot saved as 'chart_inspection.png'")
            
            # Inspect chart elements
            print("\n📊 INSPECTING CHART ELEMENTS:")
            
            # Check for shapes (blackout periods)
            shapes = await page.query_selector_all('.shape-group')
            print(f"🔲 Shape groups (blackout periods): {len(shapes)}")
            
            # Check for vlines (holiday lines)
            vlines = await page.query_selector_all('.vline')
            print(f"📏 Vertical lines (holidays): {len(vlines)}")
            
            # Check for bars
            bars = await page.query_selector_all('.trace.bars')
            print(f"📊 Bar traces: {len(bars)}")
            
            # Check X-axis labels
            x_labels = await page.query_selector_all('.xtick text')
            print(f"📋 X-axis labels: {len(x_labels)}")
            
            if x_labels:
                print("📝 First 5 X-axis labels:")
                for i, label in enumerate(x_labels[:5]):
                    text = await label.text_content()
                    print(f"  {i+1}. '{text}'")
            
            # Check Y-axis labels
            y_labels = await page.query_selector_all('.ytick text')
            print(f"📋 Y-axis labels: {len(y_labels)}")
            
            if y_labels:
                print("📝 First 5 Y-axis labels:")
                for i, label in enumerate(y_labels[:5]):
                    text = await label.text_content()
                    print(f"  {i+1}. '{text}'")
            
            print("\n✅ Inspection complete!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        finally:
            await browser.close()
            
            # Stop the dashboard process if we started it
            if process:
                print("🛑 Stopping dashboard...")
                process.terminate()
                process.wait()

if __name__ == "__main__":
    asyncio.run(inspect_chart())
