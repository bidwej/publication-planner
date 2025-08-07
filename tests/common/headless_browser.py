"""
Headless browser test functions for capturing web app screenshots.
"""

import asyncio
import subprocess
import time
import requests
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def is_server_running(url: str, timeout: int = 2) -> bool:
    """Check if a web server is running at the given URL."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_web_server(script_path: str, port: int, max_wait: int = 10) -> Optional[subprocess.Popen]:
    """Start a web server using the given script and wait for it to be ready."""
    print(f"🚀 Starting web server on port {port}...")
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print(f"⏳ Waiting for server to start...")
        url = f"http://127.0.0.1:{port}"
        for i in range(max_wait):
            if is_server_running(url):
                print(f"✅ Server is running at {url}!")
                return process
            time.sleep(1)
            print(f"   Waiting... ({i+1}/{max_wait})")
        
        print(f"❌ Server failed to start within {max_wait} seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

async def capture_web_page_screenshot(
    url: str,
    output_path: str,
    script_path: Optional[str] = None,
    port: Optional[int] = None,
    wait_for_selector: Optional[str] = None,
    wait_timeout: int = 5000,
    extra_wait: int = 2000,
    full_page: bool = True,
    browser_options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Capture a screenshot of a web page using headless browser.
    
    Args:
        url: URL to capture
        output_path: Path to save the screenshot
        script_path: Path to script to start server (if needed)
        port: Port number for server (if starting server)
        wait_for_selector: CSS selector to wait for before screenshot
        wait_timeout: Timeout for waiting for selector (ms)
        extra_wait: Extra time to wait after page load (ms)
        full_page: Whether to capture full page or viewport only
        browser_options: Additional browser options
    
    Returns:
        True if successful, False otherwise
    """
    
    # Check if server is running, start if needed
    server_was_running = is_server_running(url)
    process = None
    
    if not server_was_running and script_path and port:
        process = start_web_server(script_path, port)
        if not process:
            print(f"❌ Failed to start server. Please run manually:")
            print(f"   python {script_path}")
            return False
    elif not server_was_running:
        print(f"❌ Server not running at {url} and no script provided to start it")
        return False
    else:
        print(f"✅ Server is already running at {url}!")
    
    async with async_playwright() as p:
        # Launch browser with options
        browser_options = browser_options or {}
        browser = await p.chromium.launch(headless=True, **browser_options)
        page = await browser.new_page()
        
        print(f"🔍 Capturing screenshot from {url}...")
        
        try:
            # Navigate to the page
            await page.goto(url)
            print("✅ Loaded page")
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            
            # Wait for specific selector if provided
            if wait_for_selector:
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
                    print(f"✅ Found selector: {wait_for_selector}")
                except Exception as e:
                    print(f"⚠️  Selector {wait_for_selector} not found: {e}")
            
            # Extra wait for dynamic content
            if extra_wait > 0:
                await page.wait_for_timeout(extra_wait)
            
            # Take screenshot
            await page.screenshot(path=output_path, full_page=full_page)
            print(f"📸 Screenshot saved as '{output_path}'")
            
            # Inspect chart elements (optional)
            await _inspect_chart_elements(page)
            
            print("✅ Screenshot capture complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error capturing screenshot: {e}")
            return False
        
        finally:
            await browser.close()
            
            # Stop the server process if we started it
            if process:
                print("🛑 Stopping server...")
                process.terminate()
                process.wait()
                print("✅ Server stopped.")

async def _inspect_chart_elements(page: Page) -> None:
    """Inspect chart elements and print statistics."""
    print("\n📊 INSPECTING CHART ELEMENTS:")
    
    try:
        # Check for shapes (blackout periods)
        shapes = await page.query_selector_all('.shape-group')
        print(f"🔲 Shape groups (blackout periods): {len(shapes)}")
        
        # Check for vlines (holiday lines)
        vlines = await page.query_selector_all('.vline')
        print(f"📏 Vertical lines (holidays): {len(vlines)}")
        
        # Check for bars
        bars = await page.query_selector_all('.trace.bars')
        print(f"📊 Bar traces: {len(bars)}")
        
        # Check for scatter plots
        scatter = await page.query_selector_all('.trace.scatter')
        print(f"📈 Scatter traces: {len(scatter)}")
        
    except Exception as e:
        print(f"⚠️  Error inspecting elements: {e}")

async def capture_all_scheduler_options(
    base_url: str = "http://127.0.0.1:8050",
    output_dir: str = "web_charts",
    script_path: str = "run_web_dashboard.py",
    port: int = 8050
) -> Dict[str, bool]:
    """
    Capture screenshots for all scheduler options available in the web app.
    
    Args:
        base_url: Base URL of the web app
        output_dir: Directory to save screenshots
        script_path: Path to script to start server
        port: Port number for server
    
    Returns:
        Dictionary mapping scheduler names to success status
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Define scheduler options (based on main.py)
    schedulers = [
        "greedy",
        "stochastic",
        "lookahead", 
        "backtracking",
        "random",
        "heuristic",
        "optimal"
    ]
    
    results = {}
    
    # Start server if not running
    if not is_server_running(base_url):
        process = start_web_server(script_path, port)
        if not process:
            print("❌ Failed to start server")
            return {scheduler: False for scheduler in schedulers}
    else:
        process = None
        print("✅ Server is already running!")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the app
            await page.goto(base_url)
            await page.wait_for_load_state('networkidle')
            
            for scheduler in schedulers:
                try:
                    print(f"\n🔄 Capturing {scheduler} scheduler...")
                    
                    # Select the scheduler strategy
                    await page.select_option('#strategy-selector', scheduler)
                    await page.wait_for_timeout(1000)
                    
                    # Click generate button
                    await page.click('#generate-schedule-btn')
                    await page.wait_for_timeout(3000)  # Wait for chart generation
                    
                    # Take screenshot
                    screenshot_path = output_path / f"{scheduler}_scheduler.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"✅ Saved {scheduler} screenshot")
                    
                    results[scheduler] = True
                    
                except Exception as e:
                    print(f"❌ Error capturing {scheduler}: {e}")
                    results[scheduler] = False
            
            await browser.close()
    
    finally:
        # Stop server if we started it
        if process:
            print("🛑 Stopping server...")
            process.terminate()
            process.wait()
    
    return results

async def capture_timeline_screenshots(
    base_url: str = "http://127.0.0.1:8051",
    output_dir: str = "timeline_charts",
    script_path: str = "run_web_timeline.py",
    port: int = 8051
) -> bool:
    """
    Capture timeline dashboard screenshots.
    
    Args:
        base_url: Base URL of the timeline app
        output_dir: Directory to save screenshots
        script_path: Path to script to start timeline server
        port: Port number for timeline server
    
    Returns:
        True if successful, False otherwise
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Capture timeline screenshot
    success = await capture_web_page_screenshot(
        url=base_url,
        output_path=str(output_path / "timeline_dashboard.png"),
        script_path=script_path,
        port=port,
        wait_for_selector="#generate-btn",
        extra_wait=3000
    )
    
    return success
