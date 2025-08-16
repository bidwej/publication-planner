#!/usr/bin/env python3
"""
Unified runner script for the Paper Planner Web Charts.
This runs either the dashboard or timeline with optional chart generation.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import date, timedelta

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

def run_dashboard() -> int:
    """Run the dashboard normally."""
    try:
        from app.main import main
        
        # Set up arguments for dashboard mode
        sys.argv = ['main.py', '--port', '8050']
        
        # Run the main function
        main()
        return 0
        
    except ImportError as e:
        print("[ERROR] Error importing dashboard app: %s", e)
        print("[TIP] Make sure you're in the project root directory")
        return 1
    except Exception as e:
        print("[ERROR] Error starting dashboard: %s", e)
        return 1

def run_timeline() -> int:
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
            return 1
        
        # Set up arguments for timeline mode
        sys.argv = ['main.py', '--port', '8051']
        
        logger.info("[CHART] Starting timeline mode on port 8051")
        logger.info("[WEB] Timeline will be available at: http://127.0.0.1:8051")
        logger.info("[REFRESH] Press Ctrl+C to stop the server")
        logger.info("-" * 50)
        
        # Run the main function
        app_main()
        return 0
        
    except KeyboardInterrupt:
        logger.info("[STOP] Timeline server stopped by user")
        return 0
    except Exception as e:
        logger.error("[ERROR] Error starting timeline: %s", e)
        logger.error("[TIP] Check the logs for more details")
        return 1

def _create_standardized_config(timeline_range: Optional[str]) -> Dict:
    """Create a standardized config for consistent timeline ranges."""
    if not timeline_range:
        return {}  # Use default behavior
    
    # Calculate start and end dates for the specified range
    today = date.today()
    
    if timeline_range == "1year":
        start_date = today
        end_date = today + timedelta(days=365)
    elif timeline_range == "6months":
        start_date = today
        end_date = today + timedelta(days=180)
    elif timeline_range == "2years":
        start_date = today
        end_date = today + timedelta(days=730)
    else:
        # Try to parse as number of days
        try:
            days = int(timeline_range)
            start_date = today
            end_date = today + timedelta(days=days)
        except ValueError:
            print(f"[WARNING] Invalid timeline range '{timeline_range}', using default")
            return {}
    
    return {
        "timeline_start": start_date,
        "timeline_end": end_date,
        "force_timeline_range": True
    }

def _generate_chart_with_timeline_range(schedule: Dict[str, date], config, filename: str, timeline_config: Dict) -> str:
    """Generate a chart with standardized timeline range."""
    try:
        from app.components.gantt.chart import create_gantt_chart
        
        # Create the chart with the forced timeline range
        from src.core.models import ScheduleState, SchedulerStrategy
        from datetime import datetime
        
        schedule_state = ScheduleState(
            schedule=schedule,
            config=config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
        
        fig = create_gantt_chart(schedule_state)
        
        # Save as PNG
        fig.write_image(
            filename, 
            width=1200, 
            height=600, 
            scale=2,
            format='png'
        )
        
        print("✅ Gantt chart saved as %s", filename)
        return filename
    except Exception as e:
        print(f"❌ Error generating PNG: {e}")
        return ""

def generate_dashboard_charts(timeline_range: Optional[str] = None) -> Dict[str, bool]:
    """Generate actual chart PNGs for all scheduler options."""
    try:
        print("[CHART] Generating dashboard charts...")
        if timeline_range:
            print(f"[TIMELINE] Using standardized range: {timeline_range}")
        
        # Import required modules
        from src.core.config import load_config
        from src.schedulers.greedy import GreedyScheduler
        from src.schedulers.stochastic import StochasticGreedyScheduler
        from src.schedulers.lookahead import LookaheadGreedyScheduler
        from src.schedulers.backtracking import BacktrackingGreedyScheduler
        from src.schedulers.random import RandomScheduler
        from src.schedulers.heuristic import HeuristicScheduler
        from src.schedulers.optimal import OptimalScheduler
        
        # Load configuration
        config = load_config('data/config.json')
        print("[OK] Configuration loaded")
        
        # Create standardized timeline config if specified
        timeline_config = _create_standardized_config(timeline_range)
        
        # Define schedulers to test
        schedulers = {
            'greedy': GreedyScheduler(config),
            'stochastic': StochasticGreedyScheduler(config),
            'lookahead': LookaheadGreedyScheduler(config),
            'backtracking': BacktrackingGreedyScheduler(config),
            'random': RandomScheduler(config),
            'heuristic': HeuristicScheduler(config),
            'optimal': OptimalScheduler(config)
        }
        
        results = {}
        
        for scheduler_name, scheduler in schedulers.items():
            try:
                print(f"[CHART] Generating chart for {scheduler_name} scheduler...")
                
                # Generate schedule using this scheduler
                schedule = scheduler.schedule()
                
                if schedule:
                    # Generate PNG chart with standardized timeline if specified
                    filename = f"chart_{scheduler_name}.png"
                    
                    if timeline_config:
                        # Use the standardized timeline range
                        output_path = _generate_chart_with_timeline_range(
                            schedule, 
                            config, 
                            filename,
                            timeline_config
                        )
                    else:
                        # Use default behavior
                        from app.components.gantt.chart import generate_gantt_png
                        output_path = generate_gantt_png(schedule, config, filename)
                    
                    if output_path:
                        print(f"[OK] {scheduler_name} chart saved as {filename}")
                        results[scheduler_name] = True
                    else:
                        print(f"[ERROR] Failed to save {scheduler_name} chart")
                        results[scheduler_name] = False
                else:
                    print(f"[WARNING] {scheduler_name} scheduler returned no schedule")
                    results[scheduler_name] = False
                    
            except Exception as e:
                print(f"[ERROR] Error generating {scheduler_name} chart: {e}")
                results[scheduler_name] = False
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Error generating dashboard charts: {e}")
        return {}

def generate_timeline_chart(timeline_range: Optional[str] = None) -> bool:
    """Generate timeline chart PNG."""
    try:
        print("[TIMELINE] Generating timeline chart...")
        if timeline_range:
            print(f"[TIMELINE] Using standardized range: {timeline_range}")
        
        # Import required modules
        from src.core.config import load_config
        from src.schedulers.greedy import GreedyScheduler
        
        # Load configuration
        config = load_config('data/config.json')
        print("[OK] Configuration loaded")
        
        # Use greedy scheduler for timeline (fast and reliable)
        scheduler = GreedyScheduler(config)
        schedule = scheduler.schedule()
        
        if schedule:
            # Generate PNG chart with standardized timeline if specified
            filename = "timeline_chart.png"
            
            if timeline_range:
                # Create standardized timeline config
                timeline_config = _create_standardized_config(timeline_range)
                output_path = _generate_chart_with_timeline_range(
                    schedule, 
                    config, 
                    filename,
                    timeline_config
                )
            else:
                # Use default behavior
                from app.components.gantt.chart import generate_gantt_png
                output_path = generate_gantt_png(schedule, config, filename)
            
            if output_path:
                print(f"[OK] Timeline chart saved as {filename}")
                return True
            else:
                print("[ERROR] Failed to save timeline chart")
                return False
        else:
            print("[WARNING] Timeline scheduler returned no schedule")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error generating timeline chart: {e}")
        return False

def main() -> None:
    """Main entry point with mode and chart generation options."""
    parser = argparse.ArgumentParser(description="Paper Planner Web Charts Runner")
    parser.add_argument(
        '--mode',
        choices=['dashboard', 'timeline'],
        default='dashboard',
        help='Mode to run: dashboard or timeline (default: dashboard)'
    )
    parser.add_argument(
        '--generate',
        action='store_true',
        help='Generate chart PNGs and exit (works with both modes)'
    )
    parser.add_argument(
        '--timeline-range',
        choices=['1year', '6months', '2years'],
        help='Standardize timeline range for all charts (default: auto-fit to data)'
    )
    
    args = parser.parse_args()
    
    if args.generate:
        print("[START] Generating %s charts", args.mode)
        if args.mode == 'dashboard':
            results = generate_dashboard_charts(args.timeline_range)
            
            print("\n[CHART] Results:")
            for scheduler, success in results.items():
                status = "[OK]" if success else "[ERROR]"
                print("  %s %s", status, scheduler)
            
            success_count = sum(results.values())
            total_count = len(results)
            print("\n[CHART] Overall: %s/%s schedulers generated", success_count, total_count)
            
        else:
            success = generate_timeline_chart(args.timeline_range)
            if success:
                print("[OK] Timeline chart generated successfully!")
            else:
                print("[ERROR] Timeline chart generation failed!")
    else:
        if args.mode == 'dashboard':
            run_dashboard()
        else:
            run_timeline()

if __name__ == "__main__":
    main()
