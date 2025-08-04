#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from planner import Planner

def debug_scheduler():
    planner = Planner("config.json")
    
    print("=== Config ===")
    print(f"Max concurrent submissions: {planner.config['max_concurrent_submissions']}")
    print(f"Min paper lead time days: {planner.config['min_paper_lead_time_days']}")
    
    print("\n=== Submissions ===")
    for sub in planner.cfg.submissions:
        print(f"{sub.id}: {sub.title}")
        print(f"  Earliest start: {sub.earliest_start_date}")
        print(f"  Dependencies: {sub.depends_on}")
        print(f"  Conference: {sub.conference_id}")
        print()
    
    print("=== Conferences ===")
    for conf in planner.cfg.conferences:
        print(f"{conf.id}: {conf.deadlines}")
    
    # Try to schedule
    try:
        mod_sched, paper_sched = planner.schedule("greedy")
        print("=== Schedule Success ===")
        print(f"Mod schedule: {mod_sched}")
        print(f"Paper schedule: {paper_sched}")
    except Exception as e:
        print(f"=== Schedule Failed ===")
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_scheduler() 