#!/usr/bin/env python3
"""
Script to automatically inspect the Paper Planner web app using Playwright.
This will help identify issues with the chart display without needing screenshots.
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def inspect_app():
    """Inspect the web app and report on chart issues."""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        page = await browser.new_page()
        
        print("🔍 Starting web app inspection...")
        
        try:
            # Navigate to the app
            await page.goto('http://127.0.0.1:8050')
            print("✅ Successfully loaded the app")
            
            # Wait for the page to load
            await page.wait_for_load_state('networkidle')
            print("✅ Page fully loaded")
            
            # Wait for the generate button to be available
            await page.wait_for_selector('#generate-btn', timeout=10000)
            print("✅ Generate button found")
            
            # Click the generate button
            await page.click('#generate-btn')
            print("✅ Clicked generate button")
            
            # Wait for the chart to load
            await page.wait_for_timeout(3000)
            print("✅ Waited for chart generation")
            
            # Inspect the chart
            print("\n📊 INSPECTING CHART ELEMENTS:")
            
            # Check for chart container
            chart_container = await page.query_selector('#timeline-chart')
            if chart_container:
                print("✅ Chart container found")
                
                # Get chart dimensions
                chart_box = await chart_container.bounding_box()
                if chart_box:
                    print(f"📏 Chart dimensions: {chart_box['width']:.0f}x{chart_box['height']:.0f}")
                
                # Check for Plotly chart elements
                plotly_elements = await page.query_selector_all('.plotly-graph-div')
                print(f"📈 Found {len(plotly_elements)} Plotly chart elements")
                
                # Check for bars (Gantt chart bars)
                bars = await page.query_selector_all('.trace.bars')
                print(f"📊 Found {len(bars)} bar traces")
                
                # Check for annotations (arrows, deadlines)
                annotations = await page.query_selector_all('.annotation')
                print(f"🏹 Found {len(annotations)} annotations")
                
                # Check for shapes (blackout periods) - improved detection
                shapes = await page.query_selector_all('.shape-group')
                print(f"🔲 Found {len(shapes)} shape groups (blackout periods)")
                
                # Check for vertical lines (deadlines, holidays)
                vlines = await page.query_selector_all('.vline')
                print(f"📏 Found {len(vlines)} vertical lines")
                
            else:
                print("❌ Chart container not found")
            
            # Check axis labels
            print("\n📋 AXIS LABELS:")
            
            # Check Y-axis (vertical) labels
            y_axis_labels = await page.query_selector_all('.ytick text')
            print(f"📊 Y-axis labels found: {len(y_axis_labels)}")
            
            if y_axis_labels:
                print("📝 Y-axis labels (first 10):")
                for i, label in enumerate(y_axis_labels[:10]):
                    text = await label.text_content()
                    print(f"  {i+1}. '{text}'")
            
            # Check X-axis (horizontal) labels
            x_axis_labels = await page.query_selector_all('.xtick text')
            print(f"📊 X-axis labels found: {len(x_axis_labels)}")
            
            if x_axis_labels:
                print("📝 X-axis labels (first 10):")
                for i, label in enumerate(x_axis_labels[:10]):
                    text = await label.text_content()
                    print(f"  {i+1}. '{text}'")
            
            # Check for blackout periods specifically - improved detection
            print("\n🔲 BLACKOUT PERIODS:")
            
            # Look for gray rectangles in shape groups
            shape_groups = await page.query_selector_all('.shape-group')
            gray_shapes = 0
            for shape_group in shape_groups:
                paths = await shape_group.query_selector_all('path')
                for path in paths:
                    style = await path.get_attribute('style')
                    if style and 'rgb(128, 128, 128)' in style:
                        gray_shapes += 1
            print(f"🔲 Gray shapes (blackout periods): {gray_shapes}")
            
            # Look for any paths with gray fill
            all_paths = await page.query_selector_all('path')
            gray_paths = 0
            for path in all_paths:
                style = await path.get_attribute('style')
                if style and ('rgb(128, 128, 128)' in style or '128, 128, 128' in style):
                    gray_paths += 1
            print(f"🔲 Total gray-filled paths: {gray_paths}")
            
            # Check for holiday lines
            holiday_lines = await page.query_selector_all('line[stroke-dasharray]')
            print(f"🎉 Holiday lines (dashed): {len(holiday_lines)}")
            
            # Check for any lines with red color (holidays)
            all_lines = await page.query_selector_all('line')
            red_lines = 0
            for line in all_lines:
                style = await line.get_attribute('style')
                if style and 'rgb(255, 0, 0)' in style:
                    red_lines += 1
            print(f"🎉 Red lines (holidays): {red_lines}")
            
            # Take a screenshot for debugging
            await page.screenshot(path='chart_inspection.png', full_page=True)
            print("📸 Screenshot saved as 'chart_inspection.png'")
            
            # Get the chart's HTML for detailed inspection
            chart_html = await page.query_selector('#timeline-chart')
            if chart_html:
                chart_inner_html = await chart_html.inner_html()
                with open('chart_debug.html', 'w', encoding='utf-8') as f:
                    f.write(chart_inner_html)
                print("📄 Chart HTML saved as 'chart_debug.html'")
            
            print("\n✅ Inspection complete!")
            
        except Exception as e:
            print(f"❌ Error during inspection: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    # Start the web app in background if not already running
    print("🚀 Starting inspection...")
    asyncio.run(inspect_app())
