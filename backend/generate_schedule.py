#!/usr/bin/env python3
"""Generate a schedule for the Endoscope AI project."""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Import backend components
from src.core.config import load_config
from src.core.constants import SCHEDULING_CONSTANTS
from src.schedulers.base import Scheduler
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticScheduler
from src.schedulers.lookahead import LookaheadScheduler
from src.schedulers.backtracking import BacktrackingScheduler
from src.schedulers.random import RandomScheduler
from src.schedulers.heuristic import HeuristicScheduler
from src.schedulers.optimal import OptimalScheduler

# Constants from backend
DEFAULT_CONFIG_PATH = "data/config.json"
AVAILABLE_STRATEGIES = {
    "greedy": GreedyScheduler,
    "stochastic": StochasticScheduler,
    "lookahead": LookaheadScheduler,
    "backtracking": BacktrackingScheduler,
    "random": RandomScheduler,
    "heuristic": HeuristicScheduler,
    "optimal": OptimalScheduler
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


def load_configuration(config_path: str, quiet: bool = False) -> Optional[object]:
    """Load configuration using backend infrastructure."""
    if not quiet:
        print(f"Loading configuration from: {config_path}")
    
    try:
        config = load_config(config_path)
        if not quiet:
            print(f"Loaded {len(config.submissions)} submissions and {len(config.conferences)} conferences")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None


def create_scheduler(strategy: str, config: object) -> Optional[Scheduler]:
    """Create scheduler instance using backend factory."""
    try:
        scheduler_class = AVAILABLE_STRATEGIES[strategy]
        return scheduler_class(config)
    except Exception as e:
        print(f"Error creating {strategy} scheduler: {e}")
        return None


def handle_strategy_mode(strategy: str, config_path: str, quiet: bool) -> int:
    """Handle single strategy execution mode."""
    if not quiet:
        print(f"Using {strategy} scheduling strategy...")
    
    # Load configuration
    config = load_configuration(config_path, quiet)
    if not config:
        return 1
    
    # Create scheduler
    scheduler = create_scheduler(strategy, config)
    if not scheduler:
        return 1
    
    # TODO: Execute scheduling and save results
    if not quiet:
        print(f"Successfully created {strategy} scheduler")
    
    return 0


def handle_compare_mode(config_path: str, quiet: bool) -> int:
    """Handle strategy comparison mode."""
    if not quiet:
        print("Comparing multiple scheduling strategies...")
    
    # Load configuration
    config = load_configuration(config_path, quiet)
    if not config:
        return 1
    
    # TODO: Run multiple strategies and compare results
    if not quiet:
        print("Strategy comparison not yet implemented")
    
    return 0


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
        return handle_compare_mode(args.config, args.quiet)
    elif args.strategy:
        return handle_strategy_mode(args.strategy, args.config, args.quiet)
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
