"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Set
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.constraints import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import DEFAULT_ABSTRACT_ADVANCE_DAYS


@BaseScheduler.register_strategy(SchedulerStrategy.GREEDY)
class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule using greedy algorithm.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        self._auto_link_abstract_paper()
        self._validate_venue_compatibility()
        
        # Assign conferences to papers that need them
        schedule = {}
        schedule = self._assign_conferences(schedule)
        
        # Create abstract submissions for papers that need them
        schedule = self._create_abstract_submissions()
        
        # Recalculate topological order after adding abstracts
        topo = self._topological_order()
        
        # Global time window - use robust date calculation
        current, end = self._get_scheduling_window()
        
        active: Set[str] = set()
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", DEFAULT_ABSTRACT_ADVANCE_DAYS)
            self._schedule_early_abstracts(schedule, abstract_advance)
        
        while current <= end and len(schedule) < len(self.submissions):
            # Skip blackout dates
            blackout_dates = self.config.blackout_dates or []
            if not is_working_day(current, blackout_dates):
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
            
            # Sort by priority weight (greedy selection)
            ready = self._sort_by_priority(ready)
            
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
            else:
                base_priority = weights.get("mod", 1.5)
            
            return base_priority
        
        return sorted(ready, key=get_priority, reverse=True) 