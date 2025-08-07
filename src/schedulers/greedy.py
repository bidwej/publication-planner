"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Set, Optional
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.constraints import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS
from src.core.models import Submission


@BaseScheduler.register_strategy(SchedulerStrategy.GREEDY)
class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    def schedule(self) -> Dict[str, date]:
        """Generate a schedule using greedy algorithm."""
        # Auto-link abstracts to papers if needed
        self._auto_link_abstract_paper()
        
        # Get submissions in priority order
        submissions = self._topological_order()
        
        # Initialize schedule
        schedule = {}
        
        # Schedule each submission
        for submission_id in submissions:
            submission = self.config.submissions_dict[submission_id]
            
            # Find earliest valid start date
            start_date = self._find_earliest_valid_start(submission, schedule)
            
            if start_date:
                schedule[submission_id] = start_date
            else:
                # If we can't schedule this submission, skip it
                continue
        
        return schedule
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight (greedy selection)."""
        def get_priority(sid: str) -> float:
            s = self.submissions[sid]
            weights = self.config.priority_weights or {}
            
            base_priority = 0.0
            if s.kind.value == "PAPER":
                base_priority = weights.get("engineering_paper" if s.engineering else "medical_paper", 1.0)
            elif s.kind.value == "ABSTRACT":
                base_priority = weights.get("abstract", 0.5)
            elif s.kind.value == "POSTER":
                base_priority = weights.get("poster", 0.8)
            else:
                base_priority = weights.get("other", 1.0)
            
            return base_priority
        
        return sorted(ready, key=get_priority, reverse=True) 

    def _find_earliest_valid_start(self, submission: Submission, schedule: Dict[str, date]) -> Optional[date]:
        """Find the earliest valid start date for a submission with comprehensive constraint validation."""
     
        # Start with today
        current_date = date.today()
        
        # Check dependencies
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in schedule:
                    dep_end = self._get_end_date(schedule[dep_id], self.config.submissions_dict[dep_id])
                    current_date = max(current_date, dep_end)
        
        # Check earliest start date constraint
        if submission.earliest_start_date:
            current_date = max(current_date, submission.earliest_start_date)
        
        # Check deadline constraint
        if submission.conference_id:
            conf = self.config.conferences_dict.get(submission.conference_id)
            if conf and submission.kind in conf.deadlines:
                deadline = conf.deadlines[submission.kind]
                duration = submission.get_duration_days(self.config)
                latest_start = deadline - timedelta(days=duration)
                if current_date > latest_start:
                    return None  # Can't meet deadline
        
        # Check resource constraints and all other constraints
        max_concurrent = self.config.max_concurrent_submissions
        while current_date <= date.today() + timedelta(days=365):  # Reasonable limit
            # Count active submissions on this date
            active_count = 0
            for scheduled_id, start_date in schedule.items():
                scheduled_sub = self.config.submissions_dict[scheduled_id]
                end_date = self._get_end_date(start_date, scheduled_sub)
                if start_date <= current_date <= end_date:
                    active_count += 1
            
            # Check resource constraint
            if active_count >= max_concurrent:
                current_date += timedelta(days=1)
                continue
            
            # Check all other constraints using comprehensive validation
            if self._validate_all_constraints(submission, current_date, schedule):
                return current_date
            
            current_date += timedelta(days=1)
        
        return None  # Could not find valid start date 