#!/usr/bin/env python3
# generate_schedule.py
from __future__ import annotations
import sys
import platform
import argparse
import os
import json
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import load_config
from core.dates import parse_date_safe
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler
from output.console import print_schedule_summary, print_deadline_status, print_utilization_summary, print_metrics_summary
from output.tables import generate_schedule_summary_table, generate_deadline_table
from output.plots import plot_schedule, plot_utilization_chart, plot_deadline_compliance
from metrics.makespan import calculate_makespan, get_makespan_breakdown
from metrics.utilization import calculate_resource_utilization, calculate_peak_utilization_periods
from metrics.penalties import calculate_penalty_costs, get_penalty_breakdown
from metrics.deadlines import calculate_deadline_compliance, get_deadline_violations
from metrics.quality import calculate_schedule_quality_score, calculate_front_loading_score

def generate_schedule_cli() -> None:
    """Interactive CLI for schedule generation and analysis."""
    parser = argparse.ArgumentParser(description="Endoscope AI Scheduling Tool")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    parser.add_argument("--start-date", type=str, help="Crop Gantt chart start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="Crop Gantt chart end date (YYYY-MM-DD)")
    parser.add_argument("--mode", choices=["interactive", "compare", "analyze"], default="interactive", 
                       help="Mode: interactive (default), compare (all schedulers), analyze (detailed metrics)")
    parser.add_argument("--scheduler", choices=["greedy", "stochastic", "lookahead", "backtracking"], 
                       default="greedy", help="Scheduler to use (default: greedy)")
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        print(f"Loaded configuration with {len(config.submissions)} submissions and {len(config.conferences)} conferences")
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        print("Please ensure the config file exists and adjust the path.")
        return
    
    if args.mode == "compare":
        compare_all_schedulers(config, args)
    elif args.mode == "analyze":
        analyze_schedule(config, args)
    else:
        interactive_mode(config, args)

def compare_all_schedulers(config, args):
    """Compare all available schedulers."""
    schedulers = {
        "Greedy": GreedyScheduler(config),
        "Stochastic": StochasticGreedyScheduler(config),
        "Lookahead": LookaheadGreedyScheduler(config),
        "Backtracking": BacktrackingGreedyScheduler(config)
    }
    
    results = {}
    
    for name, scheduler in schedulers.items():
        print(f"\n{'='*50}")
        print(f"Testing {name} Scheduler")
        print(f"{'='*50}")
        
        try:
            schedule = scheduler.schedule()
            results[name] = schedule
            
            print_schedule_summary(schedule, config)
            print_metrics_summary(schedule, config)
            
            is_valid = scheduler.validate_schedule(schedule)
            print(f"Schedule valid: {is_valid}")
            
        except Exception as e:
            print(f"Error with {name} scheduler: {e}")
            results[name] = None
    
    # Compare results
    print(f"\n{'='*50}")
    print("COMPARISON SUMMARY")
    print(f"{'='*50}")
    
    for name, schedule in results.items():
        if schedule is None:
            print(f"{name}: Failed")
            continue
        
        makespan = calculate_makespan(schedule, config)
        utilization = calculate_resource_utilization(schedule, config)
        penalties = calculate_penalty_costs(schedule, config)
        compliance = calculate_deadline_compliance(schedule, config)
        quality = calculate_schedule_quality_score(schedule, config)
        
        print(f"\n{name}:")
        print(f"  Makespan: {makespan} days")
        print(f"  Avg Utilization: {utilization['avg_utilization']:.1%}")
        print(f"  Total Penalties: ${penalties['total_penalty']:.2f}")
        print(f"  Deadline Compliance: {compliance['compliance_rate']:.1f}%")
        print(f"  Quality Score: {quality:.3f}")

def analyze_schedule(config, args):
    """Detailed analysis of a single scheduler."""
    scheduler_map = {
        "greedy": GreedyScheduler,
        "stochastic": StochasticGreedyScheduler,
        "lookahead": LookaheadGreedyScheduler,
        "backtracking": BacktrackingGreedyScheduler
    }
    
    scheduler_class = scheduler_map.get(args.scheduler, GreedyScheduler)
    scheduler = scheduler_class(config)
    
    print(f"\n{'='*50}")
    print(f"Detailed Analysis for {args.scheduler.title()} Scheduler")
    print(f"{'='*50}")
    
    try:
        schedule = scheduler.schedule()
        
        # Generate tables
        summary_table = generate_schedule_summary_table(schedule, config)
        deadline_table = generate_deadline_table(schedule, config)
        
        print("\nSchedule Summary:")
        for row in summary_table[:10]:  # Show first 10 rows
            print(f"  {row['ID']}: {row['Title']} ({row['Start Date']} - {row['End Date']})")
        
        print("\nDeadline Status:")
        for row in deadline_table[:10]:  # Show first 10 rows
            status_color = "🟢" if row['Status'] == "On Time" else "🔴"
            print(f"  {status_color} {row['Submission']}: {row['Margin (days)']} days")
        
        # Plot schedule
        plot_schedule(
            schedule=schedule,
            submissions=config.submissions,
            start_date=parse_date_safe(args.start_date),
            end_date=parse_date_safe(args.end_date),
            save_path=None
        )
        
    except Exception as e:
        print(f"Error generating schedule: {e}")

def interactive_mode(config, args):
    """Interactive mode for schedule generation."""
    scheduler_map = {
        "greedy": GreedyScheduler,
        "stochastic": StochasticGreedyScheduler,
        "lookahead": LookaheadGreedyScheduler,
        "backtracking": BacktrackingGreedyScheduler
    }
    
    scheduler_class = scheduler_map.get(args.scheduler, GreedyScheduler)
    scheduler = scheduler_class(config)
    
    while True:
        # Generate schedule
        schedule = scheduler.schedule()
        
        # Plot it
        plot_schedule(
            schedule=schedule,
            submissions=config.submissions,
            start_date=parse_date_safe(args.start_date),
            end_date=parse_date_safe(args.end_date),
            save_path=None
        )
        
        key = _prompt_keypress()
        if key == " ":
            print("Regenerating a new schedule...")
            continue
        elif key in ("\r", "\n"):
            out_path = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(out_path, 'w') as f:
                json.dump(schedule, f, default=str, indent=2)
            print(f"Schedule saved to: {out_path}")
            break
        elif key.lower() == "q" or key == "\x1b":
            print("Exiting without saving.")
            break
        else:
            print(f"Unknown key: {repr(key)} → quitting.")
            break

def _prompt_keypress() -> str:
    # Cross-platform keypress prompt
    print("")
    print("Press SPACE to regenerate, ENTER to save schedule, or Q / ESC to quit.")
    print(">", end=" ", flush=True)
    
    try:
        if platform.system() == "Windows":
            import msvcrt
            return msvcrt.getwch()
        else:
            import termios  # pylint: disable=import-error, import-outside-toplevel
            import tty      # pylint: disable=import-error, import-outside-toplevel
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                return sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        print(f"\n[Warning] Unable to read keypress: {e}")
        return "\n"  # Default to "ENTER" behavior

if __name__ == "__main__":
    generate_schedule_cli()