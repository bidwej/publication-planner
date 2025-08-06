"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Set
from datetime import date, timedelta
from .base import BaseScheduler
from core.constraints import is_working_day
from core.models import SchedulerStrategy
from core.constants import DEFAULT_ABSTRACT_ADVANCE_DAYS


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
        topo = self._topological_order()
        
        # Global time window
        dates = [s.earliest_start_date for s in self.submissions.values() if s.earliest_start_date]
        for c in self.conferences.values():
            dates.extend(c.deadlines.values())
        if not dates:
            raise RuntimeError("No valid dates found for scheduling")
        current = min(dates)
        end = max(dates) + timedelta(days=self.config.min_paper_lead_time_days * 2)
        
        schedule: Dict[str, date] = {}
        active: Set[str] = set()
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", DEFAULT_ABSTRACT_ADVANCE_DAYS)
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
                if s.earliest_start_date and current < s.earliest_start_date:
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
            print(f"Note: Could not schedule {len(missing)} submissions: {missing}")
            print(f"Successfully scheduled {len(schedule)} out of {len(self.submissions)} submissions")
        
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