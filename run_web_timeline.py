#!/usr/bin/env python3
"""
Runner script for the Paper Planner Timeline.
This runs the timeline-only view with Gantt chart.
"""

import sys
import argparse
import asyncio
import logging
import time
from pathlib import Path

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('timeline_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

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
    """Main entry point with screenshot option."""
    parser = argparse.ArgumentParser(description="Paper Planner Timeline Runner")
    parser.add_argument(
        '--capture',
        action='store_true',
        help='Capture timeline screenshot and exit'
    )
    
    args = parser.parse_args()
    
    if args.capture:
        print("🚀 Capturing timeline screenshot...")
        asyncio.run(capture_timeline_screenshot())
    else:
        run_timeline()

if __name__ == "__main__":
    main()
