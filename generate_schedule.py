#!/usr/bin/env python3
"""Generate and analyze schedules using various algorithms."""

import sys
import os
from datetime import date
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import load_config
from src.core.models import SchedulerStrategy
from src.schedulers.base import BaseScheduler
from src.core.constraints import validate_all_constraints
from src.scoring.penalty import calculate_penalty_score
from src.scoring.quality import calculate_quality_score
from src.scoring.efficiency import calculate_efficiency_score
from src.output.console import print_schedule_summary, print_metrics_summary
from src.output.output_manager import generate_and_save_output


def analyze_schedule(schedule: Dict[str, date], config, strategy_name: str = "Unknown") -> None:
    """Analyze a schedule and print results."""
    if not schedule:
        print(f"No schedule generated for {strategy_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"SCHEDULE ANALYSIS: {strategy_name.upper()}")
    print(f"{'='*60}")
    
    # Print basic summary
    print_schedule_summary(schedule, config)
    
    # Validate constraints
    validation_result = validate_all_constraints(schedule, config)
    print(f"Constraint Validation:")
    print(f"  Deadlines: {'✓' if validation_result.deadlines.is_valid else '✗'}")
    print(f"  Dependencies: {'✓' if validation_result.dependencies.is_valid else '✗'}")
    print(f"  Resources: {'✓' if validation_result.resources.is_valid else '✗'}")
    print(f"  Overall: {'✓' if validation_result.is_valid else '✗'}")
    
    # Print metrics
    print_metrics_summary(schedule, config)
    
    # Generate and save output
    try:
        output_data = generate_and_save_output(schedule, config)
        print(f"Output saved successfully for {strategy_name}")
    except Exception as e:
        print(f"Error saving output for {strategy_name}: {e}")


def interactive_mode(config) -> None:
    """Run interactive mode for schedule generation."""
    print("\n" + "="*60)
    print("INTERACTIVE SCHEDULE GENERATOR")
    print("="*60)
    
    strategies = list(SchedulerStrategy)
    
    while True:
        print(f"\nAvailable strategies:")
        for i, strategy in enumerate(strategies, 1):
            print(f"  {i}. {strategy.value}")
        print(f"  {len(strategies) + 1}. Compare all strategies")
        print(f"  {len(strategies) + 2}. Exit")
        
        try:
            choice = input(f"\nSelect strategy (1-{len(strategies) + 2}): ").strip()
            
            if choice == str(len(strategies) + 2):
                print("Goodbye!")
                break
            elif choice == str(len(strategies) + 1):
                compare_strategies(config)
            elif choice.isdigit() and 1 <= int(choice) <= len(strategies):
                strategy = strategies[int(choice) - 1]
                generate_and_analyze_schedule(config, strategy)
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def compare_strategies(config) -> None:
    """Compare all available scheduling strategies."""
    print(f"\n{'='*60}")
    print("COMPARING ALL STRATEGIES")
    print(f"{'='*60}")
    
    results = {}
    
    for strategy in SchedulerStrategy:
        print(f"\nGenerating schedule with {strategy.value}...")
        try:
            schedule = generate_and_analyze_schedule(config, strategy, verbose=False)
            if schedule:
                results[strategy.value] = schedule
        except Exception as e:
            print(f"Error with {strategy.value}: {e}")
    
    if results:
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        for strategy_name, schedule in results.items():
            penalty = calculate_penalty_score(schedule, config)
            quality = calculate_quality_score(schedule, config)
            efficiency = calculate_efficiency_score(schedule, config)
            
            print(f"\n{strategy_name}:")
            print(f"  Penalty: ${penalty.total_penalty:.2f}")
            print(f"  Quality: {quality:.3f}")
            print(f"  Efficiency: {efficiency:.3f}")
            print(f"  Submissions: {len(schedule)}")


def generate_and_analyze_schedule(config, strategy: SchedulerStrategy, verbose: bool = True) -> Dict[str, date]:
    """Generate and analyze a schedule for the given strategy."""
    try:
        # Create scheduler
        scheduler = BaseScheduler.create_scheduler(strategy, config)
        
        # Generate schedule
        schedule = scheduler.schedule()
        
        if verbose:
            analyze_schedule(schedule, config, strategy.value)
        
        return schedule
        
    except Exception as e:
        if verbose:
            print(f"Error generating schedule with {strategy.value}: {e}")
        return {}


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = load_config()
        
        if len(sys.argv) > 1:
            # Command line mode
            strategy_name = sys.argv[1].upper()
            try:
                strategy = SchedulerStrategy(strategy_name)
                generate_and_analyze_schedule(config, strategy)
            except ValueError:
                print(f"Unknown strategy: {strategy_name}")
                print(f"Available strategies: {[s.value for s in SchedulerStrategy]}")
                sys.exit(1)
        else:
            # Interactive mode
            interactive_mode(config)
            
    except FileNotFoundError as e:
        print(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()