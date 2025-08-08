"""Random scheduler implementation for baseline comparison."""

from __future__ import annotations
import random
from typing import Dict, List, Optional
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS


@BaseScheduler.register_strategy(SchedulerStrategy.RANDOM)
class RandomScheduler(BaseScheduler):
    """Random scheduler that schedules submissions in random order for baseline comparison."""
    
    def __init__(self, config, seed: Optional[int] = None):
        """Initialize scheduler with config and optional seed."""
        super().__init__(config)
        if seed is not None:
            random.seed(seed)
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule using random selection.
        
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
            # Skip blackout dates
            if not is_working_day(current_date, self.config.blackout_dates):
                current_date += timedelta(days=1)
                continue
            
            # Update active submissions
            active = self._update_active_submissions(active, schedule, current_date)
            
            # Get ready submissions
            ready = self._get_ready_submissions(topo, schedule, current_date)
            
            # Randomize the order
            random.shuffle(ready)
            
            # Schedule submissions up to concurrency limit
            self._schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
        return schedule
