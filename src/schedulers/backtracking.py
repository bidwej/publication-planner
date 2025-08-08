"""Backtracking scheduler implementation."""

from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS


@BaseScheduler.register_strategy(SchedulerStrategy.BACKTRACKING)
class BacktrackingGreedyScheduler(GreedyScheduler):
    """Backtracking greedy scheduler that can reschedule submissions to find better solutions."""
    
    def __init__(self, config, max_backtracks: int = 5):
        """Initialize scheduler with config and max backtracks."""
        super().__init__(config)
        self.max_backtracks = max_backtracks
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule using backtracking algorithm.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        # Use shared setup
        schedule, topo, start_date, end_date = self._run_common_scheduling_setup()
        
        # Initialize active submissions list
        active: List[str] = []
        current_date = start_date
        
        while current_date <= end_date and len(schedule) < len(self.submissions):
            # Check working day constraint
            if not is_working_day(current_date, self.config.blackout_dates):
                current_date += timedelta(days=1)
                continue
            
            # Update active submissions
            active = self._update_active_submissions(active, schedule, current_date)
            
            # Get ready submissions
            ready = self._get_ready_submissions(topo, schedule, current_date)
            
            # Sort by priority
            ready = self._sort_by_priority(ready)
            
            # Try to schedule up to concurrency limit
            scheduled_this_round = self._schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            # If nothing was scheduled and we have active submissions, try backtracking
            if scheduled_this_round == 0 and active:
                if self._backtrack(schedule, active, current_date):
                    continue  # Try again with the rescheduled submission
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
        return schedule
    
    def _backtrack(self, schedule: Dict[str, date], active: List[str], current_date: date) -> bool:
        """Try to backtrack by rescheduling an active submission earlier."""
        for submission_id in list(active):
            if self._can_reschedule_earlier(submission_id, schedule, current_date):
                # Remove from active and schedule
                active.remove(submission_id)
                del schedule[submission_id]
                return True
        return False
    
    def _can_reschedule_earlier(self, submission_id: str, schedule: Dict[str, date], current_date: date) -> bool:
        """Check if a submission can be rescheduled earlier."""
        submission = self.submissions[submission_id]
        current_start = schedule[submission_id]
        
        # Try to find an earlier valid start date
        for days_back in range(1, SCHEDULING_CONSTANTS.backtrack_limit_days + 1):  # Look back up to max_backtrack_days days
            new_start = current_start - timedelta(days=days_back)
            if new_start < (submission.earliest_start_date or current_date):
                break
            
            if self._can_schedule(submission_id, new_start, schedule, []):
                schedule[submission_id] = new_start
                return True
        
        return False
    
    def _can_schedule(self, submission_id: str, start_date: date, schedule: Dict[str, date], active: List[str]) -> bool:
        """Check if a submission can be scheduled at the given start date."""
        submission = self.submissions[submission_id]
        
        # Use comprehensive validation instead of simple checks
        return self._validate_all_constraints(submission, start_date, schedule) 