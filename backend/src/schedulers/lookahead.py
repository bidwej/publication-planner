"""Lookahead scheduler implementation."""

from __future__ import annotations
from typing import List
from datetime import timedelta, date
from schedulers.greedy import GreedyScheduler
from core.dates import is_working_day
from core.models import Submission, Schedule
from core.constants import SCHEDULING_CONSTANTS


class LookaheadGreedyScheduler(GreedyScheduler):
    """Lookahead scheduler that considers future implications of decisions."""
    
    # ===== INITIALIZATION =====
    
    def __init__(self, config, lookahead_days: int = SCHEDULING_CONSTANTS.lookahead_window_days) -> None:
        """Initialize scheduler with config and lookahead buffer."""
        super().__init__(config)
        self.lookahead_days = lookahead_days
    
    # ===== PUBLIC INTERFACE METHODS =====
    
    def schedule(self) -> Schedule:
        """Generate a schedule using lookahead algorithm."""
        # Use shared setup
        self.reset_schedule()
        schedule = self.current_schedule
        topo = self.dependency_order
        start_date = self.start_date
        end_date = self.end_date
        
        # Initialize active submissions list
        active: List[str] = []
        current_date = start_date
        
        while current_date <= end_date and len(schedule) < len(self.submissions):
            # Skip blackout dates
            if not is_working_day(current_date, self.config.blackout_dates):
                current_date += timedelta(days=1)
                continue
            
            # Update active submissions
            active = self.update_active_submissions(active, schedule, current_date)
            
            # Get ready submissions
            ready = self.get_ready_submissions(topo, schedule, current_date)
            
            # Sort by lookahead priority
            ready = sorted(ready, key=lambda sid: self.get_priority(self.submissions[sid]), reverse=True)
            
            # Schedule submissions up to concurrency limit
            self.schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self.print_scheduling_summary(schedule)
        
        return schedule
    
    # ===== OVERRIDDEN METHODS =====
    
    def get_priority(self, submission: Submission) -> float:
        """Calculate priority with lookahead consideration."""
        base_priority = super().get_priority(submission)
        
        # Add lookahead bonus for submissions that enable many others
        lookahead_bonus = 0.0
        if submission.depends_on:
            # Check how many submissions depend on this one
            dependent_count = sum(1 for s in self.submissions.values() 
                                if s.depends_on and submission.id in s.depends_on)
            lookahead_bonus = dependent_count * 0.1  # Small bonus per dependent
        
        return base_priority + lookahead_bonus
    
    def can_schedule(self, submission: Submission, start_date: date, schedule: Schedule) -> bool:
        """Check if submission can be scheduled with lookahead validation."""
        if not super().can_schedule(submission, start_date, schedule):
            return False
        
        # Additional lookahead validation: check if scheduling this submission
        # would block future high-priority submissions
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id not in schedule:
                    # Check if this dependency is high priority
                    dep = self.submissions.get(dep_id)
                    if dep and self.get_priority(dep) > self.get_priority(submission):
                        # High priority dependency not scheduled yet
                        return False
        
        return True 
