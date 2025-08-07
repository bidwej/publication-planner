#!/usr/bin/env python3
"""
Unified runner script for the Paper Planner Web Charts.
This runs either the dashboard or timeline with optional screenshot capture.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
import os
os.environ['PYTHONPATH'] = str(Path(__file__).parent) + os.pathsep + os.environ.get('PYTHONPATH', '')

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web_charts_server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def run_dashboard():
    """Run the dashboard normally."""
    try:
        from app.main import main
        
        # Set up arguments for dashboard mode
        sys.argv = ['main.py', '--mode', 'dashboard']
        
        # Run the main function
        main()
        
    except ImportError as e:
        print("[ERROR] Error importing dashboard app: %s", e)
        print("[TIP] Make sure you're in the project root directory")
        sys.exit(1)
    except Exception as e:
        print("[ERROR] Error starting dashboard: %s", e)
        sys.exit(1)

def run_timeline():
    """Run the timeline normally."""
    try:
        logger.info("[START] Starting Paper Planner Timeline Server")
        
        # Check if we can import the main module
        try:
            from app.main import main as app_main
            logger.info("[OK] Successfully imported app.main")
        except ImportError as e:
            logger.error("[ERROR] Error importing timeline app: %s", e)
            logger.error("[TIP] Make sure you're in the project root directory")
            logger.error("[TIP] Check that all dependencies are installed")
            sys.exit(1)
        
        # Set up arguments for timeline mode
        sys.argv = ['main.py', '--mode', 'timeline', '--port', '8051']
        
        logger.info("[CHART] Starting timeline mode on port 8051")
        logger.info("[WEB] Timeline will be available at: http://127.0.0.1:8051")
        logger.info("[REFRESH] Press Ctrl+C to stop the server")
        logger.info("-" * 50)
        
        # Run the main function
        app_main()
        
    except KeyboardInterrupt:
        logger.info("[STOP] Timeline server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("[ERROR] Error starting timeline: %s", e)
        logger.error("[TIP] Check the logs for more details")
        sys.exit(1)

async def capture_dashboard_screenshots():
    """Capture screenshots of all dashboard schedulers."""
    try:
        from tests.common.headless_browser import capture_all_scheduler_options
        
        print("[CHART] Capturing dashboard screenshots")
        results = await capture_all_scheduler_options()
        
        print("\n[SCATTER] Results:")
        for scheduler, success in results.items():
            status = "[OK]" if success else "[ERROR]"
            print("  %s %s", status, scheduler)
        
        success_count = sum(results.values())
        total_count = len(results)
        print("\n[CHART] Overall: %s/%s schedulers captured", success_count, total_count)
        
    except Exception as e:
        print("[ERROR] Error capturing screenshots: %s", e)
        sys.exit(1)

async def capture_timeline_screenshot():
    """Capture screenshot of the timeline."""
    try:
        from tests.common.headless_browser import capture_timeline_screenshots
        
        print("[TIMELINE] Capturing timeline screenshot")
        success = await capture_timeline_screenshots()
        
        if success:
            print("[OK] Timeline screenshot captured successfully!")
        else:
            print("[ERROR] Timeline screenshot capture failed!")
            
    except Exception as e:
        print("[ERROR] Error capturing timeline screenshot: %s", e)
        sys.exit(1)

def main():
    """Main entry point with mode and screenshot options."""
    parser = argparse.ArgumentParser(description="Paper Planner Web Charts Runner")
    parser.add_argument(
        '--mode',
        choices=['dashboard', 'timeline'],
        default='dashboard',
        help='Mode to run: dashboard or timeline (default: dashboard)'
    )
    parser.add_argument(
        '--capture',
        action='store_true',
        help='Capture screenshots and exit (works with both modes)'
    )
    
    args = parser.parse_args()
    
    if args.capture:
        print("[START] Capturing %s screenshots", args.mode)
        if args.mode == 'dashboard':
            asyncio.run(capture_dashboard_screenshots())
        else:
            asyncio.run(capture_timeline_screenshot())
    else:
        if args.mode == 'dashboard':
            run_dashboard()
        else:
            run_timeline()

if __name__ == "__main__":
    main()
