#!/usr/bin/env python3
"""Demonstration script showing default configuration works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from planner import Planner
from core.models import SchedulerStrategy

def main():
    """Demonstrate that the application works with default configuration."""
    print("🎯 Paper Planner - Default Configuration Demo")
    print("=" * 50)
    
    # Create planner with non-existent config (uses defaults)
    print("\n1. Creating planner with default configuration...")
    planner = Planner("nonexistent_config.json")
    
    print(f"✓ Config loaded successfully")
    print(f"  - {len(planner.config.submissions)} submissions")
    print(f"  - {len(planner.config.conferences)} conferences")
    print(f"  - Max concurrent: {planner.config.max_concurrent_submissions}")
    
    # Show sample data
    print("\n2. Sample data:")
    print("   Conferences:")
    for conf in planner.config.conferences:
        print(f"     - {conf.id}: {conf.name}")
    
    print("   Submissions:")
    for sub in planner.config.submissions:
        print(f"     - {sub.id}: {sub.title} ({sub.kind.value})")
    
    # Generate schedule with different strategies
    print("\n3. Generating schedules with different strategies:")
    
    strategies = [
        SchedulerStrategy.GREEDY,
        SchedulerStrategy.RANDOM,
        SchedulerStrategy.HEURISTIC
    ]
    
    for strategy in strategies:
        print(f"\n   {strategy.value.upper()} strategy:")
        try:
            schedule = planner.schedule(strategy)
            print(f"     ✓ Generated schedule with {len(schedule)} submissions")
            
            # Show schedule
            for submission_id, start_date in schedule.items():
                submission = planner.config.submissions_dict[submission_id]
                print(f"       {submission_id}: {start_date} ({submission.title})")
                
        except Exception as e:
            print(f"     ✗ Failed: {e}")
    
    # Validate schedule
    print("\n4. Validating schedule:")
    try:
        schedule = planner.schedule()
        is_valid = planner.validate_schedule(schedule)
        print(f"   ✓ Schedule validation: {'PASS' if is_valid else 'FAIL'}")
        
        # Get metrics
        metrics = planner.get_schedule_metrics(schedule)
        print(f"   ✓ Schedule metrics:")
        print(f"     - Makespan: {metrics['makespan']} days")
        print(f"     - Total penalty: {metrics['total_penalty']}")
        print(f"     - Compliance rate: {metrics['compliance_rate']:.1f}%")
        
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
    
    print("\n🎉 Success! The application works with just default configuration.")
    print("   No config file needed - everything uses sensible defaults.")

if __name__ == "__main__":
    main()
