#!/usr/bin/env python3
"""
Inspect the chart and generate PNG to see what's wrong.
"""

import sys
import os
import asyncio
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

async def inspect_chart():
    """Inspect the chart and generate PNG."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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

if __name__ == "__main__":
    asyncio.run(inspect_chart())
