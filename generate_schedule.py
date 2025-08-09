#!/usr/bin/env python3
"""
Generate a schedule for the Endoscope AI project.

This script loads configuration data and generates a schedule using the scheduler.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import date

# Add the src directory to the path
os.environ['PYTHONPATH'] = str(Path(__file__).parent / "src") + os.pathsep + os.environ.get('PYTHONPATH', '')

# Import after adding src to path - pylint: disable=wrong-import-position
from src.core.config import load_config
from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler
from src.analytics.console import print_schedule_analysis, print_strategy_comparison, print_available_strategies
from src.analytics.exporters.csv_exporter import CSVExporter

# Import all schedulers to register them with the factory
import src.schedulers.greedy
import src.schedulers.stochastic
import src.schedulers.lookahead
import src.schedulers.backtracking
import src.schedulers.random
import src.schedulers.heuristic
import src.schedulers.optimal

# Manual registration as backup for optimal scheduler
from src.schedulers.optimal import OptimalScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.OPTIMAL] = OptimalScheduler

# Explicit registration of all schedulers to ensure they're available
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.schedulers.lookahead import LookaheadGreedyScheduler
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.schedulers.random import RandomScheduler
from src.schedulers.heuristic import HeuristicScheduler

BaseScheduler._strategy_registry[SchedulerStrategy.GREEDY] = GreedyScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.STOCHASTIC] = StochasticGreedyScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.LOOKAHEAD] = LookaheadGreedyScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.BACKTRACKING] = BacktrackingGreedyScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.RANDOM] = RandomScheduler
BaseScheduler._strategy_registry[SchedulerStrategy.HEURISTIC] = HeuristicScheduler
# Advanced scheduler removed as per requirements


def generate_schedule(config, strategy: SchedulerStrategy, verbose: bool = True, csv_dir: Optional[str] = None) -> Dict[str, date]:
    """Generate a schedule for the given strategy."""
    try:
        if verbose:
            print(f"Creating scheduler for strategy: {strategy}")
            print(f"Registry contains: {list(BaseScheduler._strategy_registry.keys())}")
        scheduler = BaseScheduler.create_scheduler(strategy, config)
        if verbose:
            print(f"Scheduler created successfully: {type(scheduler).__name__}")
        schedule = scheduler.schedule()
        
        if verbose:
            print_schedule_analysis(schedule, config, strategy.value)
        
        # Export CSV if directory specified
        if csv_dir and schedule:
            csv_exporter = CSVExporter(config)
            csv_files = csv_exporter.export_all_csv(schedule, csv_dir)
            if verbose:
                print(f"\nCSV files exported to {csv_dir}:")
                for file_type, filepath in csv_files.items():
                    if filepath:
                        print(f"  - {file_type}: {filepath}")
        
        return schedule
    except Exception as e:
        if verbose:
            print(f"Error generating schedule with {strategy.value}: {e}")
        return {}


def compare_all_strategies(config, output_file: Optional[str] = None) -> None:
    """Compare all available scheduling strategies."""
    print("\n%s", '='*60)
    print("COMPARING ALL STRATEGIES")
    print("%s", '='*60)
    
    results = {}
    for strategy in SchedulerStrategy:
        print("\nGenerating schedule with %s", strategy.value)
        schedule = generate_schedule(config, strategy, verbose=False)
        if schedule:
            results[strategy.value] = schedule
    
    if results:
        print_strategy_comparison(results, config, output_file)


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a schedule for the Endoscope AI project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --strategy greedy
  %(prog)s --strategy stochastic --config custom_config.json
  %(prog)s --compare --output comparison.json
  %(prog)s --list-strategies
        """
    )
    
    parser.add_argument('--strategy', '-s', type=str, help='Scheduling strategy to use')
    parser.add_argument('--config', '-c', type=str, default='config.json', help='Path to configuration file')
    parser.add_argument('--compare', '-C', action='store_true', help='Compare all available strategies')
    parser.add_argument('--output', '-o', type=str, help='Output file for comparison results')
    parser.add_argument('--csv-dir', type=str, help='Directory to save CSV exports')
    parser.add_argument('--list-strategies', '-l', action='store_true', help='List all available strategies')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle list strategies
    if args.list_strategies:
        print_available_strategies()
        return
    
    # Validate arguments
    if not args.strategy and not args.compare:
        parser.error("Either --strategy or --compare must be specified. Use --list-strategies to see available options.")
    
    if args.strategy and args.compare:
        parser.error("Cannot use both --strategy and --compare. Choose one.")
    
    try:
        config = load_config(args.config)
        
        if args.compare:
            compare_all_strategies(config, args.output)
        else:
            try:
                strategy = SchedulerStrategy(args.strategy.lower())
                generate_schedule(config, strategy, verbose=not args.quiet, csv_dir=args.csv_dir)
            except ValueError:
                print("Unknown strategy: %s", args.strategy)
                print("Available strategies: %s", [s.value for s in SchedulerStrategy])
                sys.exit(1)
            
    except FileNotFoundError as e:
        print("Configuration file not found: %s", e)
        sys.exit(1)
    except Exception as e:
        print("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()