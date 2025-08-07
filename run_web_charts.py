#!/usr/bin/env python3
"""
Unified runner script for the Paper Planner Web Charts.
This runs either the dashboard or timeline with optional screenshot capture.
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web_charts_server.log')
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
        print(f"❌ Error importing dashboard app: {e}")
        print("💡 Make sure you're in the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)

def run_timeline():
    """Run the timeline normally."""
    try:
        logger.info("🚀 Starting Paper Planner Timeline Server...")
        
        # Check if we can import the main module
        try:
            from app.main import main as app_main
            logger.info("✅ Successfully imported app.main")
        except ImportError as e:
            logger.error(f"❌ Error importing timeline app: {e}")
            logger.error("💡 Make sure you're in the project root directory")
            logger.error("💡 Check that all dependencies are installed")
            sys.exit(1)
        
        # Set up arguments for timeline mode
        sys.argv = ['main.py', '--mode', 'timeline', '--port', '8051']
        
        logger.info("📊 Starting timeline mode on port 8051")
        logger.info("🌐 Timeline will be available at: http://127.0.0.1:8051")
        logger.info("🔄 Press Ctrl+C to stop the server")
        logger.info("-" * 50)
        
        # Run the main function
        app_main()
        
    except KeyboardInterrupt:
        logger.info("🛑 Timeline server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error starting timeline: {e}")
        logger.error("💡 Check the logs for more details")
        sys.exit(1)

async def capture_dashboard_screenshots():
    """Capture screenshots of all dashboard schedulers."""
    try:
        from tests.common.headless_browser import capture_all_scheduler_options
        
        print("📊 Capturing dashboard screenshots...")
        results = await capture_all_scheduler_options()
        
        print("\n📈 Results:")
        for scheduler, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {scheduler}")
        
        success_count = sum(results.values())
        total_count = len(results)
        print(f"\n📊 Overall: {success_count}/{total_count} schedulers captured")
        
    except Exception as e:
        print(f"❌ Error capturing screenshots: {e}")
        sys.exit(1)

async def capture_timeline_screenshot():
    """Capture screenshot of the timeline."""
    try:
        from tests.common.headless_browser import capture_timeline_screenshots
        
        print("📅 Capturing timeline screenshot...")
        success = await capture_timeline_screenshots()
        
        if success:
            print("✅ Timeline screenshot captured successfully!")
        else:
            print("❌ Timeline screenshot capture failed!")
            
    except Exception as e:
        print(f"❌ Error capturing timeline screenshot: {e}")
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
        print(f"🚀 Capturing {args.mode} screenshots...")
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
