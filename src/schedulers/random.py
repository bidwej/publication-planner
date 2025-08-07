"""Random scheduler implementation for baseline comparison."""

from __future__ import annotations
import random
from typing import Dict, List, Set, Optional
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.constraints import is_working_day
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
        self._auto_link_abstract_paper()
        self._validate_venue_compatibility()
        topo = self._topological_order()
        
        # Global time window - use robust date calculation
        current, end = self._get_scheduling_window()
        
        schedule: Dict[str, date] = {}
        active: Set[str] = set()
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", SCHEDULING_CONSTANTS.default_abstract_advance_days)
            self._schedule_early_abstracts(schedule, abstract_advance)
        
        while current <= end and len(schedule) < len(self.submissions):
            # Skip blackout dates
            if not is_working_day(current, self.config.blackout_dates):
                current += timedelta(days=1)
                continue
            
            # Retire finished drafts
            active = {
                sid for sid in active
                if self._get_end_date(schedule[sid], self.submissions[sid]) > current
            }
            
            # Gather ready submissions
            ready: List[str] = []
            for sid in topo:
                if sid in schedule:
                    continue
                s = self.submissions[sid]
                if not self._deps_satisfied(s, schedule, current):
                    continue
                # Use calculated earliest start date
                earliest_start = self._calculate_earliest_start_date(s)
                if current < earliest_start:
                    continue
                ready.append(sid)
            
            # Randomize the order
            random.shuffle(ready)
            
            # Try to schedule up to concurrency limit
            for sid in ready:
                if len(active) >= self.config.max_concurrent_submissions:
                    break
                if not self._meets_deadline(self.submissions[sid], current):
                    continue
                schedule[sid] = current
                active.add(sid)
            
            current += timedelta(days=1)
        
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            print("Note: Could not schedule %s submissions: %s", len(missing), missing)
            print("Successfully scheduled %s out of %s submissions", len(schedule), len(self.submissions))
        
        return schedule
