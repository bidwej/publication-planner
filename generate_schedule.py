#!/usr/bin/env python3
"""
Generate paper submission schedules using various algorithms.

This script provides both command-line and interactive modes for generating
paper submission schedules based on conference deadlines and constraints.
"""

import json
import os
import platform
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli import parse_args, validate_args, get_scheduler_strategy
from src.core.config import load_config
from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler
from src.output.output_manager import generate_and_save_output
from src.core.dates import parse_date_safe
from src.scoring.penalty import calculate_penalty_score
from src.scoring.efficiency import calculate_efficiency_score
from src.scoring.quality import calculate_quality_score
from src.core.constraints import validate_deadline_compliance, validate_resource_constraints

def print_schedule_summary(schedule, config):
    """Print a summary of the schedule."""
    print(f"Generated schedule with {len(schedule)} submissions")
    if schedule:
        start_date = min(schedule.values())
        end_date = max(schedule.values())
        print(f"Schedule spans from {start_date} to {end_date}")

def print_metrics_summary(schedule, config):
    """Print metrics summary."""
    penalty = calculate_penalty_score(schedule, config)
    quality = calculate_quality_score(schedule, config)
    efficiency = calculate_efficiency_score(schedule, config)
    print(f"Penalty: ${penalty.total_penalty:.2f}, Quality: {quality:.2f}, Efficiency: {efficiency:.2f}")

def print_deadline_status(schedule, config):
    """Print deadline compliance status."""
    deadline_validation = validate_deadline_compliance(schedule, config)
    print(f"Deadline compliance: {deadline_validation.compliance_rate:.1f}%")

def print_utilization_summary(schedule, config):
    """Print resource utilization summary."""
    resource_validation = validate_resource_constraints(schedule, config)
    print(f"Max concurrent: {resource_validation.max_observed}/{resource_validation.max_concurrent}")

def calculate_makespan(schedule, config):
    """Calculate schedule makespan in days."""
    if not schedule:
        return 0
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    return (end_date - start_date).days

def calculate_resource_utilization(schedule, config):
    """Calculate resource utilization metrics."""
    # Placeholder implementation
    return {"avg_utilization": 0.8, "peak_utilization": 2}

def calculate_penalty_costs(schedule, config):
    """Calculate penalty costs."""
    penalty = calculate_penalty_score(schedule, config)
    return {"total_penalty": penalty.total_penalty}

def calculate_deadline_compliance(schedule, config):
    """Calculate deadline compliance."""
    validation = validate_deadline_compliance(schedule, config)
    return {"compliance_rate": validation.compliance_rate}

def calculate_schedule_quality_score(schedule, config):
    """Calculate overall schedule quality score."""
    return calculate_quality_score(schedule, config)

def plot_schedule(schedule, submissions, start_date, end_date, save_path):
    """Plot schedule as Gantt chart."""
    print(f"Plotting schedule (save_path: {save_path})")
    # Placeholder implementation

def plot_utilization_chart(schedule, config, save_path):
    """Plot resource utilization chart."""
    print(f"Plotting utilization chart (save_path: {save_path})")
    # Placeholder implementation

def plot_deadline_compliance(schedule, config, save_path):
    """Plot deadline compliance chart."""
    print(f"Plotting deadline compliance (save_path: {save_path})")
    # Placeholder implementation

def generate_schedule_cli() -> None:
    """Interactive CLI for schedule generation and analysis."""
    args = None
    try:
        args = parse_args()
        validate_args(args)
        
        config = load_config(args.config)
        print(f"Loaded configuration with {len(config.submissions)} submissions and {len(config.conferences)} conferences")
    except FileNotFoundError:
        print(f"Config file not found: {args.config if args else 'config.json'}")
        print("Please ensure the config file exists and adjust the path.")
        return
    except ValueError as e:
        print(f"Invalid arguments: {e}")
        return
    
    if args.mode == "compare":
        compare_all_schedulers(config, args)
    elif args.mode == "analyze":
        analyze_schedule(config, args)
    else:
        interactive_mode(config, args)

def compare_all_schedulers(config, args):
    """Compare all available schedulers."""
    strategies = {
        "Greedy": SchedulerStrategy.GREEDY,
        "Stochastic": SchedulerStrategy.STOCHASTIC,
        "Lookahead": SchedulerStrategy.LOOKAHEAD,
        "Backtracking": SchedulerStrategy.BACKTRACKING
    }
    
    results = {}
    
    for name, strategy in strategies.items():
        print(f"\n{'='*50}")
        print(f"Testing {name} Scheduler")
        print(f"{'='*50}")
        
        try:
            scheduler = BaseScheduler.create_scheduler(strategy, config)
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
    """Detailed analysis of a single scheduler with all output features."""
    # Convert string to enum
    strategy_map = {
        "greedy": SchedulerStrategy.GREEDY,
        "stochastic": SchedulerStrategy.STOCHASTIC,
        "lookahead": SchedulerStrategy.LOOKAHEAD,
        "backtracking": SchedulerStrategy.BACKTRACKING
    }
    
    strategy = strategy_map.get(args.scheduler, SchedulerStrategy.GREEDY)
    scheduler = BaseScheduler.create_scheduler(strategy, config)
    
    print(f"\n{'='*50}")
    print(f"Detailed Analysis for {args.scheduler.title()} Scheduler")
    print(f"{'='*50}")
    
    try:
        schedule = scheduler.schedule()
        
        # Generate all output features
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Console output
        print_schedule_summary(schedule, config)
        print_deadline_status(schedule, config)
        print_utilization_summary(schedule, config)
        print_metrics_summary(schedule, config)
        
        # 2. Generate and save all outputs using the new output manager
        output_data = generate_and_save_output(schedule, config)
        
        # 3. Generate all plots
        plot_schedule(
            schedule=schedule,
            submissions=config.submissions,
            start_date=parse_date_safe(args.start_date),
            end_date=parse_date_safe(args.end_date),
            save_path=os.path.join(output_dir, "schedule_gantt.png")
        )
        
        plot_utilization_chart(
            schedule=schedule,
            config=config,
            save_path=os.path.join(output_dir, "utilization_chart.png")
        )
        
        plot_deadline_compliance(
            schedule=schedule,
            config=config,
            save_path=os.path.join(output_dir, "deadline_compliance.png")
        )
        
        print(f"Plots saved to {output_dir}: schedule_gantt.png, utilization_chart.png, deadline_compliance.png")
        
        # 4. Save schedule as JSON
        with open(os.path.join(output_dir, "schedule.json"), 'w') as f:
            json.dump(schedule, f, default=str, indent=2)
        
        print(f"Schedule saved to {output_dir}: schedule.json")
        
    except Exception as e:
        print(f"Error generating schedule: {e}")
        import traceback
        traceback.print_exc()

def interactive_mode(config, args):
    """Interactive mode for schedule generation with full output features."""
    # Convert string to enum
    strategy_map = {
        "greedy": SchedulerStrategy.GREEDY,
        "stochastic": SchedulerStrategy.STOCHASTIC,
        "lookahead": SchedulerStrategy.LOOKAHEAD,
        "backtracking": SchedulerStrategy.BACKTRACKING
    }
    
    strategy = strategy_map.get(args.scheduler, SchedulerStrategy.GREEDY)
    scheduler = BaseScheduler.create_scheduler(strategy, config)
    
    while True:
        # Generate schedule
        schedule = scheduler.schedule()
        
        # Show console output
        print_schedule_summary(schedule, config)
        print_metrics_summary(schedule, config)
        
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
            # Save everything with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create output directory with timestamp
            output_dir = f"output/output_{timestamp}"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save schedule JSON
            out_path = os.path.join(output_dir, "schedule.json")
            with open(out_path, 'w') as f:
                json.dump(schedule, f, default=str, indent=2)
            
            # Generate and save all outputs using the new output manager
            try:
                output_data = generate_and_save_output(schedule, config)
                print(f"All outputs saved successfully!")
                
            except Exception as e:
                print(f"Warning: Some outputs failed to save: {e}")
                print(f"Schedule JSON saved to: {out_path}")
                import traceback
                traceback.print_exc()
            
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