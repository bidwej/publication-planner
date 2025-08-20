"""Random scheduler implementation for baseline comparison."""

from __future__ import annotations
import random
from typing import Dict, List, Optional
from datetime import date, timedelta
from schedulers.base import BaseScheduler
from core.dates import is_working_day
from core.models import SchedulerStrategy, Schedule
from core.constants import SCHEDULING_CONSTANTS


class RandomScheduler(BaseScheduler):
    """Random scheduler that schedules submissions in random order for baseline comparison."""
    
    def __init__(self, config, seed: Optional[int] = None):
        """Initialize scheduler with config and optional seed."""
        super().__init__(config)
        if seed is not None:
            random.seed(seed)
    
    def schedule(self) -> Schedule:
        """
        Generate a schedule using random selection.
        
        Returns
        -------
        Schedule
            Schedule object with intervals for all submissions
        """
        # Get what we need from base
        topo = self.get_dependency_order()
        start_date, end_date = self.get_scheduling_window()
        
        # Initialize empty Schedule object
        schedule = Schedule()
        
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
            
            # Randomize the order
            random.shuffle(ready)
            
            # Schedule submissions up to concurrency limit
            self.schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self.print_scheduling_summary(schedule)
        
        return schedule
