"""Backtracking scheduler implementation."""

from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from schedulers.greedy import GreedyScheduler
from core.dates import is_working_day
from core.models import SchedulerStrategy, Schedule
from core.constants import SCHEDULING_CONSTANTS


class BacktrackingGreedyScheduler(GreedyScheduler):
    """Backtracking scheduler with rescheduling capabilities."""
    
    # ===== INITIALIZATION =====
    
    def __init__(self, config, max_backtracks: int = 5) -> None:
        """Initialize scheduler with config and max backtracks."""
        super().__init__(config)
        self.max_backtracks = max_backtracks
    
    # ===== OVERRIDDEN METHODS =====
    
    def schedule(self) -> Schedule:
        """Generate a schedule using backtracking algorithm."""
        # Use shared setup from base class
        self.reset_schedule()
        schedule = self.current_schedule
        topo = self.dependency_order
        start_date = self.start_date
        end_date = self.end_date
        
        # Initialize active submissions list
        active: List[str] = []
        current_date = start_date
        
        while current_date <= end_date and len(schedule) < len(self.submissions):
            # Check working day constraint only if enabled
            if (self.config.scheduling_options and 
                self.config.scheduling_options.get("enable_working_days_only", False) and
                not is_working_day(current_date, self.config.blackout_dates)):
                current_date += timedelta(days=1)
                continue
            
            # Update active submissions
            active = self.update_active_submissions(active, schedule, current_date)
            
            # Get ready submissions
            ready = self.get_ready_submissions(topo, schedule, current_date)
            
            # Sort by priority (use base class method)
            ready = self.sort_ready_submissions(ready)
            
            # Try to schedule up to concurrency limit
            scheduled_this_round = self.schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            # If nothing was scheduled and we have active submissions, try backtracking
            if scheduled_this_round == 0 and active:
                if self._backtrack(schedule, active, current_date):
                    continue  # Try again with the rescheduled submission
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self.print_scheduling_summary(schedule)
        
        return schedule
    
    # ===== BACKTRACKING-SPECIFIC METHODS =====
    
    def _backtrack(self, schedule: Schedule, active: List[str], current_date: date) -> bool:
        """Try to backtrack by rescheduling an active submission earlier."""
        for submission_id in list(active):
            if self._can_reschedule_earlier(submission_id, schedule, current_date):
                # Remove from active and schedule
                active.remove(submission_id)
                # Remove interval from schedule
                if submission_id in schedule.intervals:
                    del schedule.intervals[submission_id]
                return True
        return False
    
    def _can_reschedule_earlier(self, submission_id: str, schedule: Schedule, current_date: date) -> bool:
        """Check if a submission can be rescheduled earlier."""
        submission = self.submissions[submission_id]
        # Use the correct Schedule.intervals structure
        if submission_id not in schedule.intervals:
            return False
            
        current_start = schedule.intervals[submission_id].start_date
        
        # Try to find an earlier valid start date
        for days_back in range(1, SCHEDULING_CONSTANTS.backtrack_limit_days + 1):  # Look back up to max_backtrack_days days
            new_start = current_start - timedelta(days=days_back)
            if new_start < (submission.earliest_start_date or current_date):
                break
            
            if self.can_schedule(self.submissions[submission_id], new_start, schedule):
                # Add the rescheduled submission
                submission = self.submissions[submission_id]
                schedule.add_interval(submission_id, new_start, duration_days=submission.get_duration_days(self.config))
                return True
        
        return False
    
 
