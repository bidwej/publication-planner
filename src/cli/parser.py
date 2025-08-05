"""Argument parsing for the paper planner CLI."""

import argparse
from ..models import SchedulerStrategy


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