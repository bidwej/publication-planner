"""Argument validation for the paper planner CLI."""

import argparse


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