"""Command-line interface for the paper planner system."""

from __future__ import annotations
import argparse
from typing import Optional
from .core.models import SchedulerStrategy

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Endoscope AI Scheduling Tool")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.json", 
        help="Path to config.json"
    )
    parser.add_argument(
        "--start-date", 
        type=str, 
        help="Crop Gantt chart start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", 
        type=str, 
        help="Crop Gantt chart end date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--mode", 
        choices=["interactive", "compare", "analyze"], 
        default="interactive", 
        help="Mode: interactive (default), compare (all schedulers), analyze (detailed metrics)"
    )
    parser.add_argument(
        "--scheduler", 
        choices=["greedy", "stochastic", "lookahead", "backtracking"], 
        default="greedy", 
        help="Scheduler to use (default: greedy)"
    )
    
    return parser

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args()

def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    if args.start_date:
        try:
            from datetime import datetime
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format")
    
    if args.end_date:
        try:
            from datetime import datetime
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format")
    
    if args.start_date and args.end_date:
        from datetime import datetime
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
        end = datetime.strptime(args.end_date, "%Y-%m-%d")
        if start >= end:
            raise ValueError("start_date must be before end_date")

def get_scheduler_strategy(scheduler_name: str) -> SchedulerStrategy:
    """Convert scheduler name to enum."""
    strategy_map = {
        "greedy": SchedulerStrategy.GREEDY,
        "stochastic": SchedulerStrategy.STOCHASTIC,
        "lookahead": SchedulerStrategy.LOOKAHEAD,
        "backtracking": SchedulerStrategy.BACKTRACKING
    }
    return strategy_map.get(scheduler_name, SchedulerStrategy.GREEDY) 