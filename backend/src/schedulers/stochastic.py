"""Stochastic scheduler implementation."""

from __future__ import annotations
import random
from typing import List
from datetime import timedelta
from schedulers.greedy import GreedyScheduler
from core.models import Submission, Schedule
from core.constants import EFFICIENCY_CONSTANTS
from core.dates import is_working_day


class StochasticGreedyScheduler(GreedyScheduler):
    """Stochastic scheduler that adds randomness to priority selection."""
    
    # ===== INITIALIZATION =====
    
    def __init__(self, config, randomness_factor: float = EFFICIENCY_CONSTANTS.randomness_factor) -> None:
        """Initialize scheduler with config and randomness factor."""
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    # ===== PUBLIC INTERFACE METHODS =====
    
    def schedule(self) -> Schedule:
        """Generate a schedule using stochastic algorithm."""
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
            
            # Sort by stochastic priority
            ready = sorted(ready, key=lambda sid: self.get_priority(self.submissions[sid]), reverse=True)
            
            # Schedule submissions up to concurrency limit
            self.schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self.print_scheduling_summary(schedule)
        
        return schedule
    
    # ===== OVERRIDDEN METHODS =====
    
    def get_priority(self, submission: Submission) -> float:
        """Calculate priority with stochastic variation."""
        base_priority = super().get_priority(submission)
        
        # Add stochastic variation to avoid getting stuck in local optima
        import random
        random.seed(hash(submission.id) % 1000)  # Deterministic but varied
        stochastic_factor = random.uniform(0.9, 1.1)  # ±10% variation
        
        return base_priority * stochastic_factor 
