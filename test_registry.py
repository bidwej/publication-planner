#!/usr/bin/env python3
"""Test script to check scheduler registry functionality."""

try:
    from src.schedulers.base import BaseScheduler
    print("✓ Successfully imported BaseScheduler")
    print(f"Registry empty: {len(BaseScheduler._strategy_registry) == 0}")
    print(f"Registry contents: {list(BaseScheduler._strategy_registry.keys())}")
    
    # Test auto-registration
    from src.core.models import SchedulerStrategy
    print(f"\nTesting auto-registration for GREEDY strategy...")
    
    # This should trigger auto-registration
    scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, None)
    print(f"✓ Successfully created GREEDY scheduler: {type(scheduler).__name__}")
    
    print(f"\nRegistry after auto-registration: {list(BaseScheduler._strategy_registry.keys())}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
