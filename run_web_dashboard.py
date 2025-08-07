#!/usr/bin/env python3
"""
Runner script for the Paper Planner Dashboard.
This runs the full dashboard with all features.
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

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

def main():
    """Main entry point with screenshot option."""
    parser = argparse.ArgumentParser(description="Paper Planner Dashboard Runner")
    parser.add_argument(
        '--capture',
        action='store_true',
        help='Capture screenshots of all schedulers and exit'
    )
    
    args = parser.parse_args()
    
    if args.capture:
        print("🚀 Capturing dashboard screenshots...")
        asyncio.run(capture_dashboard_screenshots())
    else:
        run_dashboard()

if __name__ == "__main__":
    main()
