#!/usr/bin/env python3
"""Paper Planner Backend Runner - Comprehensive backend operations launcher."""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import date

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

def setup_env():
    """Set up environment for backend imports."""
    backend_src = Path(__file__).parent / "src"
    if not backend_src.exists():
        print(f"❌ Backend source not found at {backend_src}")
        return False
    
    if str(backend_src) not in sys.path:
        sys.path.insert(0, str(backend_src))
        os.environ['PYTHONPATH'] = str(backend_src)
    
    try:
        from core.models import Config
        from core.config import load_config
        print("✓ Backend environment ready")
        return True
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
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

def run_analyze_operation(args: argparse.Namespace) -> int:
    """Run schedule analysis operation."""
    try:
        from analytics import analyze_schedule_with_scoring
        from core.config import load_config
        
        print(f"\n🔍 Analyzing schedule data")
        print(f"📁 Config: {args.config}")
        print("-" * 50)
        
        config = load_config(args.config)
        
        # Load existing schedule if available
        schedule_file = args.schedule or "output/latest_schedule.json"
        schedule = None
        
        if Path(schedule_file).exists():
            import json
            with open(schedule_file, 'r') as f:
                schedule_data = json.load(f)
                # Convert to Schedule object if it's a dict
                if isinstance(schedule_data, dict) and 'intervals' in schedule_data:
                    from core.models import Schedule, Interval
                    schedule = Schedule()
                    for sid, interval_data in schedule_data['intervals'].items():
                        start_date = date.fromisoformat(interval_data['start_date'])
                        end_date = date.fromisoformat(interval_data['end_date'])
                        schedule.intervals[sid] = Interval(start_date=start_date, end_date=end_date)
                elif isinstance(schedule_data, dict):
                    # Legacy format - convert to Schedule
                    from core.models import Schedule, Interval
                    schedule = Schedule()
                    for sid, start_date_str in schedule_data.items():
                        start_date = date.fromisoformat(start_date_str) if isinstance(start_date_str, str) else start_date_str
                        # Assume 1 day duration for legacy format
                        end_date = start_date
                        schedule.intervals[sid] = Interval(start_date=start_date, end_date=end_date)
                else:
                    schedule = schedule_data
            print(f"📅 Loaded schedule with {len(schedule.intervals) if schedule else 0} submissions")
        else:
            print("⚠️  No existing schedule found, analyzing configuration only")
        
        # Run comprehensive analysis
        analysis = analyze_schedule_with_scoring(schedule, config)
        
        print(f"\n📊 Analysis Results:")
        print(f"  Completeness: {analysis['completeness'].completion_rate:.1f}% ({analysis['completeness'].scheduled_count}/{analysis['completeness'].total_count})")
        print(f"  Distribution: {analysis['distribution'].summary}")
        
        if args.output:
            analysis_result = {
                "completeness": {
                    "scheduled_count": analysis['completeness'].scheduled_count,
                    "total_count": analysis['completeness'].total_count,
                    "completion_rate": analysis['completeness'].completion_rate,
                    "missing_submissions": analysis['completeness'].missing_submissions
                },
                "distribution": {
                    "monthly": analysis['distribution'].monthly_distribution,
                    "quarterly": analysis['distribution'].quarterly_distribution,
                    "yearly": analysis['distribution'].yearly_distribution
                }
            }
            
            import json
            with open(args.output, 'w') as f:
                json.dump(analysis_result, f, indent=2, default=str)
            print(f"\n📄 Analysis saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def run_validate_operation(args: argparse.Namespace) -> int:
    """Run validation operation."""
    try:
        from core.config import load_config
        from src.validation.schedule import validate_schedule_constraints
        from src.validation.deadline import validate_deadline_constraints
        from src.validation.resources import validate_resources_constraints
        from src.validation.config import validate_config
        
        print(f"\n✅ Validating configuration and constraints")
        print(f"📁 Config: {args.config}")
        print("-" * 50)
        
        config = load_config(args.config)
        
        # Validate configuration
        validation_result = validate_config(config)
        if not validation_result.is_valid:
            print("❌ Configuration validation failed:")
            for error in validation_result.metadata.get("errors", []):
                print(f"  - {error}")
            return 1
        else:
            print("✓ Configuration validation passed")
        
        # Validate constraints if schedule exists
        schedule_file = args.schedule or "output/latest_schedule.json"
        if Path(schedule_file).exists():
            import json
            with open(schedule_file, 'r') as f:
                schedule = json.load(f)
            
            print(f"\n📅 Validating schedule with {len(schedule)} submissions...")
            
            # Validate all constraints
            validation_result = validate_schedule_constraints(schedule, config)
            
            all_valid = True
            for constraint_type, result in validation_result["constraints"].items():
                status = "✓" if result.get("is_valid", True) else "❌"
                print(f"  {status} {constraint_type}: {result.get('summary', 'N/A')}")
                if not result.get("is_valid", True):
                    all_valid = False
            
            if all_valid:
                print("\n🎉 All constraints validated successfully!")
            else:
                print("\n⚠️  Some constraint violations found")
                return 1
        else:
            print("⚠️  No schedule file found for constraint validation")
        
        return 0
        
    except Exception as e:
        print(f"❌ Validation operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def run_monitor_operation(args: argparse.Namespace) -> int:
    """Run monitoring operation."""
    try:
        from monitoring.progress import ProgressTracker
        from monitoring.rescheduler import DynamicRescheduler
        from core.config import load_config
        
        print(f"\n📊 Monitoring schedule progress")
        print(f"📁 Config: {args.config}")
        print("-" * 50)
        
        config = load_config(args.config)
        
        # Initialize monitoring components
        progress_tracker = ProgressTracker(config)
        rescheduler = DynamicRescheduler(config, progress_tracker)
        
        # Load current schedule
        schedule_file = args.schedule or "output/latest_schedule.json"
        if Path(schedule_file).exists():
            import json
            with open(schedule_file, 'r') as f:
                schedule = json.load(f)
            
            print(f"📅 Current schedule: {len(schedule)} submissions")
            
            # Track progress
            if args.track_progress:
                # Add the schedule to progress tracker first
                progress_tracker.add_planned_schedule(schedule)
                progress_report = progress_tracker.generate_progress_report()
                print(f"\n📈 Progress Summary:")
                print(f"  Total: {progress_report.total_submissions}")
                print(f"  Completed: {progress_report.completed_submissions}")
                print(f"  In Progress: {progress_report.in_progress_submissions}")
                print(f"  Delayed: {progress_report.delayed_submissions}")
                print(f"  On Time: {progress_report.on_time_submissions}")
                print(f"  Completion: {progress_report.completion_rate:.1f}%")
                print(f"  On Time Rate: {progress_report.on_time_rate:.1f}%")
            
            # Check for deviations
            deviations = progress_tracker.detect_deviations()
            if deviations:
                print(f"\n⚠️  Schedule Deviations:")
                for deviation in deviations[:5]:  # Show top 5
                    print(f"  - {deviation['submission_id']}: {deviation['type']} ({deviation['days_delayed']} days)")
            else:
                print("\n✅ No schedule deviations detected")
        
        return 0
        
    except Exception as e:
        print(f"❌ Monitoring operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def run_export_operation(args: argparse.Namespace) -> int:
    """Run export operation."""
    try:
        from exporters.csv_exporter import CSVExporter
        from core.config import load_config
        
        print(f"\n📤 Exporting schedule data")
        print(f"📁 Config: {args.config}")
        print(f"📊 Format: {args.format}")
        print(f"📁 Output: {args.output}")
        print("-" * 50)
        
        config = load_config(args.config)
        
        # Load schedule
        schedule_file = args.schedule or "output/latest_schedule.json"
        if not Path(schedule_file).exists():
            print("❌ No schedule file found for export")
            return 1
        
        import json
        with open(schedule_file, 'r') as f:
            schedule_data = json.load(f)
        
        # Convert to Schedule object if needed
        if isinstance(schedule_data, dict) and 'intervals' in schedule_data:
            from core.models import Schedule, Interval
            schedule = Schedule()
            for sid, interval_data in schedule_data['intervals'].items():
                start_date = date.fromisoformat(interval_data['start_date'])
                end_date = date.fromisoformat(interval_data['end_date'])
                schedule.intervals[sid] = Interval(start_date=start_date, end_date=end_date)
        elif isinstance(schedule_data, dict):
            # Legacy format - convert to Schedule
            from core.models import Schedule, Interval
            schedule = Schedule()
            for sid, start_date_str in schedule_data.items():
                start_date = date.fromisoformat(start_date_str) if isinstance(start_date_str, str) else start_date_str
                # Assume 1 day duration for legacy format
                end_date = start_date
                schedule.intervals[sid] = Interval(start_date=start_date, end_date=end_date)
        else:
            schedule = schedule_data
        
        # Export based on format
        if args.format == 'csv':
            # Create output directory if it doesn't exist
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # CSV export with intervals
            import csv
            csv_file = output_dir / "schedule.csv"
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Submission ID', 'Start Date', 'End Date', 'Duration (days)'])
                for submission_id, interval in schedule.intervals.items():
                    duration = (interval.end_date - interval.start_date).days + 1
                    writer.writerow([submission_id, interval.start_date, interval.end_date, duration])
            
            print(f"\n📄 CSV export saved to: {csv_file}")
        
        elif args.format == 'json':
            # Create output directory if it doesn't exist
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / "schedule_export.json"
            with open(output_file, 'w') as f:
                json.dump(schedule_data, f, indent=2)
            print(f"\n📄 JSON export saved to: {output_file}")
        
        else:
            print(f"❌ Unsupported format: {args.format}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Export operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def run_console_operation(args: argparse.Namespace) -> int:
    """Run console interface operation."""
    try:
        from console import print_schedule_summary, print_deadline_status, print_utilization_summary
        
        print(f"\n💻 Console Interface")
        print(f"📁 Config: {args.config}")
        print("-" * 50)
        
        if args.interactive:
            print("Interactive mode not yet implemented")
            print("Use --help for available commands")
        else:
            # Show available console functions
            print("Available console functions:")
            print("  - print_schedule_summary()")
            print("  - print_deadline_status()")
            print("  - print_utilization_summary()")
            print("\nUse --interactive for interactive mode")
        
        return 0
        
    except Exception as e:
        print(f"❌ Console operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Paper Planner Backend - Comprehensive backend operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s schedule --strategy greedy --config data/config.json
  %(prog)s analyze --config data/config.json --output analysis.json
  %(prog)s validate --config data/config.json --verbose
  %(prog)s monitor --config data/config.json --track-progress
  %(prog)s export --format csv --output exports/ --config data/config.json
  %(prog)s console --config data/config.json --interactive
        """
    )
    
    # Main operation argument
    parser.add_argument(
        'operation',
        choices=OPERATIONS.keys(),
        help='Backend operation to perform'
    )
    
    # Common arguments
    parser.add_argument(
        '--config',
        type=str,
        default='data/config.json',
        help='Configuration file path (default: data/config.json)'
    )
    parser.add_argument(
        '--schedule',
        type=str,
        help='Schedule file path for operations that need it'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file/directory path'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output with error details'
    )
    
    # Operation-specific arguments
    parser.add_argument(
        '--strategy',
        choices=['greedy', 'stochastic', 'lookahead', 'backtracking', 'random', 'heuristic', 'optimal'],
        help='Scheduling strategy (for schedule operation)'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare multiple strategies (for schedule operation)'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Export format (for export operation)'
    )
    parser.add_argument(
        '--track-progress',
        action='store_true',
        help='Track schedule progress (for monitor operation)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Enable interactive mode (for console operation)'
    )
    
    args = parser.parse_args()
    
    # Validate operation requirements
    operation_info = OPERATIONS[args.operation]
    missing_required = []
    
    for required in operation_info['requires']:
        if required == 'strategy' and args.operation == 'schedule' and not args.strategy and not args.compare:
            missing_required.append('strategy (or --compare)')
        elif required == 'config' and not args.config:
            missing_required.append('config file')
    
    if missing_required:
        print(f"❌ Missing required arguments for {args.operation}: {', '.join(missing_required)}")
        print(f"\nExamples for {args.operation}:")
        for example in operation_info['examples']:
            print(f"  {sys.argv[0]} {args.operation} {example}")
        return 1
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"❌ Configuration file not found: {args.config}")
        return 1
    
    # Setup environment
    if not setup_env():
        return 1
    
    # Run the selected operation
    operation_functions = {
        'schedule': run_schedule_operation,
        'analyze': run_analyze_operation,
        'validate': run_validate_operation,
        'monitor': run_monitor_operation,
        'export': run_export_operation,
        'console': run_console_operation
    }
    
    try:
        return operation_functions[args.operation](args)
    except KeyboardInterrupt:
        print(f"\n⏹️  {args.operation} operation interrupted")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error in {args.operation}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
