#!/usr/bin/env python3
"""Generate a schedule for the Endoscope AI project."""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add src to Python path for CLI execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import backend components
from core.config import load_config
from core.constants import SCHEDULING_CONSTANTS
from core.models import SchedulerStrategy
from schedulers.base import BaseScheduler
from core.config import load_config
from core.models import SchedulerStrategy
from console import print_schedule_summary, print_deadline_status, print_utilization_summary
from reports import generate_schedule_report

# Constants from backend
DEFAULT_CONFIG_PATH = "data/config.json"
AVAILABLE_STRATEGIES = {
    "greedy": SchedulerStrategy.GREEDY,
    "stochastic": SchedulerStrategy.STOCHASTIC,
    "lookahead": SchedulerStrategy.LOOKAHEAD,
    "backtracking": SchedulerStrategy.BACKTRACKING,
    "random": SchedulerStrategy.RANDOM,
    "heuristic": SchedulerStrategy.HEURISTIC,
    "optimal": SchedulerStrategy.OPTIMAL
}


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a schedule for the Endoscope AI project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s --strategy greedy
  %(prog)s --compare
  %(prog)s --list-strategies
  %(prog)s --config {DEFAULT_CONFIG_PATH}

Default config: {DEFAULT_CONFIG_PATH}
        """
    )
    
    # Core functionality arguments
    parser.add_argument(
        "--strategy",
        choices=list(AVAILABLE_STRATEGIES.keys()),
        help="Scheduling strategy to use"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare multiple strategies"
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available scheduling strategies"
    )
    
    # Configuration and output arguments
    parser.add_argument(
        "--config", 
        type=str, 
        default=DEFAULT_CONFIG_PATH,
        help=f"Configuration file path (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    
    return parser


def validate_arguments(args: argparse.Namespace) -> Optional[str]:
    """Validate command line arguments and return error message if invalid."""
    # Check for conflicting arguments
    if args.strategy and args.compare:
        return "Cannot use --strategy and --compare together"
    
    # Validate config file if specified
    if args.config and not Path(args.config).exists():
        return f"Configuration file '{args.config}' not found"
    
    return None


def list_available_strategies() -> None:
    """Display all available scheduling strategies."""
    print("Available scheduling strategies:")
    for strategy in AVAILABLE_STRATEGIES.keys():
        print(f"  - {strategy}")


def handle_strategy_mode(strategy: str, config_path: str, output_path: Optional[str], quiet: bool) -> int:
    """Handle single strategy execution mode."""
    if not quiet:
        print(f"Using {strategy} scheduling strategy...")
    
    try:
        # Load configuration directly
        config = load_config(config_path)
        
        # Get the strategy enum
        strategy_enum = AVAILABLE_STRATEGIES[strategy]
        
        # Create scheduler and generate schedule
        if not quiet:
            print(f"Generating schedule using {strategy} strategy...")
        
        scheduler = BaseScheduler.create_scheduler(strategy_enum, config)
        schedule = scheduler.schedule()
        
        if not schedule or len(schedule.intervals) == 0:
            print("Error: No schedule was generated")
            return 1
        
        # Calculate basic metrics
        total_submissions = len(schedule.intervals)
        duration_days = schedule.calculate_duration_days()
        
        # Display results
        if not quiet:
            print(f"\nSchedule generated successfully!")
            print(f"Total submissions: {total_submissions}")
            print(f"Duration: {duration_days} days")
            
            # Print detailed console output
            print_schedule_summary(schedule, config)
            print_deadline_status(schedule, config)
            print_utilization_summary(schedule, config)
        
        # Save output if requested
        if output_path:
            if not quiet:
                print(f"\nSaving schedule to: {output_path}")
            
            # Save schedule as JSON
            output_file = Path(output_path)
            if output_file.suffix.lower() == '.json':
                import json
                schedule_data = {
                    'strategy': strategy,
                    'total_submissions': total_submissions,
                    'duration_days': duration_days,
                    'intervals': {sid: {'start_date': str(interval.start_date), 'end_date': str(interval.end_date)} 
                                 for sid, interval in schedule.intervals.items()}
                }
                with open(output_file, 'w') as f:
                    json.dump(schedule_data, f, indent=2, default=str)
            else:
                # Generate simple text report
                with open(output_file, 'w') as f:
                    f.write(f"Schedule generated using {strategy} strategy\n")
                    f.write(f"Total submissions: {total_submissions}\n")
                    f.write(f"Duration: {duration_days} days\n\n")
                    for sid, interval in schedule.intervals.items():
                        f.write(f"{sid}: {interval.start_date} to {interval.end_date}\n")
            
            if not quiet:
                print(f"Schedule saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        return 1


def handle_compare_mode(config_path: str, output_path: Optional[str], quiet: bool) -> int:
    """Handle strategy comparison mode."""
    if not quiet:
        print("Comparing multiple scheduling strategies...")
    
    try:
        # Load configuration directly
        config = load_config(config_path)
        
        results = {}
        
        # Run each strategy
        for strategy_name, strategy_enum in AVAILABLE_STRATEGIES.items():
            if not quiet:
                print(f"\nTesting {strategy_name} strategy...")
            
            try:
                scheduler = BaseScheduler.create_scheduler(strategy_enum, config)
                schedule = scheduler.schedule()
                if schedule and len(schedule.intervals) > 0:
                    total_submissions = len(schedule.intervals)
                    duration_days = schedule.calculate_duration_days()
                    results[strategy_name] = {
                        'schedule': schedule,
                        'total_submissions': total_submissions,
                        'duration_days': duration_days,
                        'success': True
                    }
                else:
                    results[strategy_name] = {'success': False, 'error': 'No schedule generated'}
            except Exception as e:
                results[strategy_name] = {'success': False, 'error': str(e)}
        
        # Display comparison
        if not quiet:
            print("\n=== Strategy Comparison Results ===")
            for strategy_name, result in results.items():
                if result['success']:
                    print(f"\n{strategy_name.upper()}:")
                    print(f"  Submissions: {result['total_submissions']}")
                    print(f"  Duration: {result['duration_days']} days")
                else:
                    print(f"\n{strategy_name.upper()}: FAILED - {result['error']}")
        
        # Save comparison results if requested
        if output_path:
            if not quiet:
                print(f"\nSaving comparison results to: {output_path}")
            
            # Save as JSON
            output_file = Path(output_path)
            if output_file.suffix.lower() == '.json':
                import json
                # Convert results to serializable format
                serializable_results = {}
                for strategy_name, result in results.items():
                    if result['success']:
                        serializable_results[strategy_name] = {
                            'success': True,
                            'total_submissions': result['total_submissions'],
                            'duration_days': result['duration_days']
                        }
                    else:
                        serializable_results[strategy_name] = result
                
                with open(output_file, 'w') as f:
                    json.dump(serializable_results, f, indent=2, default=str)
            else:
                # Generate text comparison report
                with open(output_file, 'w') as f:
                    f.write("Strategy Comparison Results\n")
                    f.write("=" * 50 + "\n\n")
                    for strategy_name, result in results.items():
                        f.write(f"{strategy_name.upper()}:\n")
                        if result['success']:
                            f.write(f"  Submissions: {result['total_submissions']}\n")
                            f.write(f"  Duration: {result['duration_days']} days\n")
                        else:
                            f.write(f"  FAILED: {result['error']}\n")
                        f.write("\n")
            
            if not quiet:
                print(f"Comparison results saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error comparing strategies: {e}")
        return 1


def execute_scheduling_workflow(args: argparse.Namespace) -> int:
    """Execute the main scheduling workflow based on arguments."""
    # Handle list-strategies command
    if args.list_strategies:
        list_available_strategies()
        return 0
    
    # Validate arguments before proceeding
    error_msg = validate_arguments(args)
    if error_msg:
        print(f"Error: {error_msg}")
        return 1
    
    # Execute main logic
    if args.compare:
        return handle_compare_mode(args.config, args.output, args.quiet)
    elif args.strategy:
        return handle_strategy_mode(args.strategy, args.config, args.output, args.quiet)
    else:
        # No valid arguments provided
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Execute workflow
    result = execute_scheduling_workflow(args)
    
    # Show help if no valid arguments were provided
    if result == 1 and not any([args.list_strategies, args.compare, args.strategy]):
        parser.print_help()
    
    return result


if __name__ == "__main__":
    sys.exit(main())
