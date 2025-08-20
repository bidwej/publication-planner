#!/usr/bin/env python3
"""Paper Planner Backend Runner - Clean version using proper package imports."""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Backend operation configuration
OPERATIONS = {
    'schedule': {
        'desc': 'Generate schedule using specified strategy',
        'requires': ['strategy', 'config'],
        'examples': ['--strategy greedy', '--strategy optimal --compare']
    },
    'analyze': {
        'desc': 'Analyze existing schedule and generate reports',
        'requires': ['config'],
        'examples': ['--config data/config.json', '--output analysis_report.json']
    },
    'validate': {
        'desc': 'Validate configuration and constraints',
        'requires': ['config'],
        'examples': ['--config data/config.json', '--verbose']
    },
    'monitor': {
        'desc': 'Monitor schedule progress and suggest rescheduling',
        'requires': ['config'],
        'examples': ['--config data/config.json', '--track-progress']
    },
    'export': {
        'desc': 'Export schedule data in various formats',
        'requires': ['config'],
        'examples': ['--format csv', '--format json', '--output exports/']
    },
    'console': {
        'desc': 'Interactive console interface for schedule operations',
        'requires': ['config'],
        'examples': ['--config data/config.json', '--interactive']
    }
}

def check_backend_installation():
    """Check if backend is properly installed."""
    try:
        from core.models import Config
        from core.config import load_config
        print("✓ Backend environment ready")
        return True
    except ImportError as e:
        print(f"❌ Backend not installed properly: {e}")
        print("Please run: python setup_dev.py")
        return False

def run_schedule_operation(args: argparse.Namespace) -> int:
    """Run schedule generation operation."""
    try:
        from schedulers.base import BaseScheduler
        from core.config import load_config
        from console import print_schedule_summary, print_deadline_status, print_utilization_summary
        from reports import generate_schedule_report
        
        print(f"\n🚀 Generating schedule with {args.strategy} strategy")
        print(f"📁 Config: {args.config}")
        print(f"📊 Output: {args.output or 'default'}")
        print("-" * 50)
        
        # Load configuration
        config = load_config(args.config)
        
        if args.compare:
            # Compare multiple strategies
            strategies = ['greedy', 'stochastic', 'lookahead', 'backtracking', 'random', 'heuristic', 'optimal']
            results = {}
            
            for strategy in strategies:
                print(f"\n📈 Testing {strategy} strategy...")
                try:
                    # Convert string to SchedulerStrategy enum
                    from core.models import SchedulerStrategy
                    strategy_enum = SchedulerStrategy(strategy)
                    scheduler = BaseScheduler.create_scheduler(strategy_enum, config)
                    schedule = scheduler.schedule()
                    if schedule and len(schedule.intervals) > 0:
                        # Calculate basic metrics
                        total_submissions = len(schedule.intervals)
                        duration_days = schedule.calculate_duration_days()
                        print(f"  ✓ {strategy}: {total_submissions} submissions, duration: {duration_days} days")
                        results[strategy] = {
                            'total_submissions': total_submissions,
                            'duration_days': duration_days
                        }
                    else:
                        print(f"  ❌ {strategy}: Failed to generate schedule")
                except Exception as e:
                    print(f"  ❌ {strategy}: Error - {e}")
            
            # Show comparison
            if results:
                print("\n📊 Strategy Comparison:")
                # Sort by duration (shorter is better)
                sorted_results = sorted(results.items(), key=lambda x: x[1]['duration_days'])
                for strategy, metrics in sorted_results:
                    print(f"  {strategy}: {metrics['total_submissions']} submissions, {metrics['duration_days']} days")
        else:
            # Single strategy
            from core.models import SchedulerStrategy
            strategy_enum = SchedulerStrategy(args.strategy)
            scheduler = BaseScheduler.create_scheduler(strategy_enum, config)
            schedule = scheduler.schedule()
            if not schedule or len(schedule.intervals) == 0:
                print("❌ Failed to generate schedule")
                return 1
            
            # Display results
            print_schedule_summary(schedule, config)
            print_deadline_status(schedule, config)
            print_utilization_summary(schedule, config)
            
            # Generate report
            if args.output:
                import json
                # Convert schedule to JSON format
                schedule_for_json = {
                    'strategy': args.strategy,
                    'total_submissions': len(schedule.intervals),
                    'duration_days': schedule.calculate_duration_days(),
                    'intervals': {sid: {'start_date': str(interval.start_date), 'end_date': str(interval.end_date)} 
                                 for sid, interval in schedule.intervals.items()}
                }
                with open(args.output, 'w') as f:
                    json.dump(schedule_for_json, f, indent=2)
                print(f"\n📄 Schedule saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Schedule operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(description="Paper Planner Backend Operations")
    
    # Add arguments
    parser.add_argument('--strategy', choices=['greedy', 'stochastic', 'lookahead', 'backtracking', 'random', 'heuristic', 'optimal'], help='Scheduling strategy')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--compare', action='store_true', help='Compare multiple strategies')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Check installation
    if not check_backend_installation():
        return 1
    
    # Run operation
    if args.strategy or args.compare:
        return run_schedule_operation(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
