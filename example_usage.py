#!/usr/bin/env python3
"""
Example usage of the refactored paper planner system.
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import load_config
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

def main():
    """Demonstrate the new modular structure."""
    
    # Load configuration
    config_path = "data/config.json"  # Adjust path as needed
    try:
        config = load_config(config_path)
        print(f"Loaded configuration with {len(config.submissions)} submissions and {len(config.conferences)} conferences")
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        print("Please ensure the config file exists and adjust the path in this script.")
        return
    
    # Test different schedulers
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
            # Generate schedule
            schedule = scheduler.schedule()
            results[name] = schedule
            
            # Print basic summary
            print_schedule_summary(schedule, config)
            
            # Print detailed metrics
            print_metrics_summary(schedule, config)
            
            # Validate schedule
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
    
    # Generate detailed tables for the best scheduler
    best_scheduler = max(results.keys(), key=lambda k: 
        calculate_schedule_quality_score(results[k], config) if results[k] else 0)
    
    if results[best_scheduler]:
        print(f"\n{'='*50}")
        print(f"Detailed Analysis for {best_scheduler}")
        print(f"{'='*50}")
        
        schedule = results[best_scheduler]
        
        # Generate tables
        summary_table = generate_schedule_summary_table(schedule, config)
        deadline_table = generate_deadline_table(schedule, config)
        
        print("\nSchedule Summary:")
        for row in summary_table[:5]:  # Show first 5 rows
            print(f"  {row['ID']}: {row['Title']} ({row['Start Date']} - {row['End Date']})")
        
        print("\nDeadline Status:")
        for row in deadline_table[:5]:  # Show first 5 rows
            status_color = "🟢" if row['Status'] == "On Time" else "🔴"
            print(f"  {status_color} {row['Submission']}: {row['Margin (days)']} days")
    
    print(f"\n{'='*50}")
    print("Refactoring Complete!")
    print("The codebase now follows the modular structure:")
    print("  - core/: Data structures and configuration")
    print("  - schedulers/: Different scheduling algorithms")
    print("  - metrics/: Schedule analysis and evaluation")
    print("  - output/: Tables, plots, and console output")
    print(f"{'='*50}")

if __name__ == "__main__":
    main() 