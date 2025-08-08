"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS
from src.core.models import Submission


@BaseScheduler.register_strategy(SchedulerStrategy.GREEDY)
class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    def schedule(self) -> Dict[str, date]:
        """Generate a schedule using greedy algorithm."""
        # Use shared setup
        schedule, topo, start_date, end_date = self._run_common_scheduling_setup()
        
        # Schedule each submission in priority order
        for submission_id in topo:
            if submission_id in schedule:
                continue
                
            submission = self.submissions[submission_id]
            
            # Find earliest valid start date
            start_date = self._find_earliest_valid_start(submission, schedule)
            
            if start_date:
                schedule[submission_id] = start_date
            else:
                # If we can't schedule this submission, skip it
                continue
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
        return schedule
    
    def _find_earliest_valid_start(self, submission: Submission, schedule: Dict[str, date]) -> Optional[date]:
        """Find the earliest valid start date for a submission with comprehensive constraint validation."""
     
        # Start with today
        current_date = date.today()
        
        # Check dependencies
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in schedule:
                    dep_end = self._get_end_date(schedule[dep_id], self.submissions[dep_id])
                    current_date = max(current_date, dep_end)
        
        # Check earliest start date constraint
        if submission.earliest_start_date:
            current_date = max(current_date, submission.earliest_start_date)
        
        # Check deadline constraint
        if submission.conference_id:
            conf = self.conferences.get(submission.conference_id)
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
            for scheduled_id, scheduled_start_date in schedule.items():
                scheduled_sub = self.submissions[scheduled_id]
                end_date = self._get_end_date(scheduled_start_date, scheduled_sub)
                if scheduled_start_date <= current_date <= end_date:
                    active_count += 1
            
            # Check resource constraint
            if active_count >= max_concurrent:
                current_date += timedelta(days=1)
                continue
            
            # Check working day constraint
            if not is_working_day(current_date, self.config.blackout_dates):
                current_date += timedelta(days=1)
                continue
            
            # Check all other constraints using comprehensive validation
            if self._validate_all_constraints(submission, current_date, schedule):
                return current_date
            
            current_date += timedelta(days=1)
        
        return None  # Could not find valid start date 