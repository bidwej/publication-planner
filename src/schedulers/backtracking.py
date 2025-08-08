"""Backtracking greedy scheduler implementation."""

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
    """Backtracking greedy scheduler that can undo decisions when stuck."""
    
    def __init__(self, config, max_backtracks: int = 5):
        super().__init__(config)
        self.max_backtracks = max_backtracks
    
    def schedule(self) -> Dict[str, date]:
        """Generate schedule with backtracking capability."""
        self._auto_link_abstract_paper()
        from src.validation.venue import _validate_venue_compatibility
        _validate_venue_compatibility(self.submissions, self.conferences)
        topo = self._topological_order()
        
        # Global time window - use robust date calculation
        current, end = self._get_scheduling_window()
        
        schedule: Dict[str, date] = {}
        active: List[str] = []
        backtracks = 0
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", SCHEDULING_CONSTANTS.abstract_advance_days)
            self._schedule_early_abstracts(schedule, abstract_advance)
        
        while current <= end and len(schedule) < len(self.submissions) and backtracks < self.max_backtracks:
            # Skip blackout dates
            if not is_working_day(current, self.config.blackout_dates):
                current += timedelta(days=1)
                continue
            
            # Retire finished drafts
            active = [
                sid for sid in active
                if self._get_end_date(schedule[sid], self.submissions[sid]) > current
            ]
            
            # Try to schedule submissions
            scheduled_this_round = self._try_schedule_round(current, topo, schedule, active)
            
            # Try backtracking if needed
            if not scheduled_this_round and active and backtracks < self.max_backtracks:
                if self._backtrack(schedule, active, current):
                    backtracks += 1
                    continue
            
            current += timedelta(days=1)
        
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            print("Note: Could not schedule %s submissions: %s", len(missing), missing)
            print("Successfully scheduled %s out of %s submissions", len(schedule), len(self.submissions))
        
        return schedule
    
    def _backtrack(self, schedule: Dict[str, date], active: List[str], current: date) -> bool:
        """Try to backtrack by rescheduling an active submission earlier."""
        for sid in list(active):
            if self._can_reschedule_earlier(sid, schedule, current):
                # Remove from active and schedule
                active.remove(sid)
                del schedule[sid]
                return True
        return False
    
    def _can_reschedule_earlier(self, sid: str, schedule: Dict[str, date], current: date) -> bool:
        """Check if a submission can be rescheduled earlier."""
        sub = self.submissions[sid]
        current_start = schedule[sid]
        
        # Try to find an earlier valid start date
        for days_back in range(1, SCHEDULING_CONSTANTS.backtrack_limit_days + 1):  # Look back up to max_backtrack_days days
            new_start = current_start - timedelta(days=days_back)
            if new_start < (sub.earliest_start_date or current):
                break
            
            if self._can_schedule(sid, new_start, schedule, []):
                schedule[sid] = new_start
                return True
        
        return False
    
    def _can_schedule(self, sid: str, start: date, schedule: Dict[str, date], active: List[str]) -> bool:
        """Check if a submission can be scheduled at the given start date."""
        sub = self.submissions[sid]
        
        # Use comprehensive validation instead of simple checks
        return self._validate_all_constraints(sub, start, schedule)
    
    def _try_schedule_round(self, current: date, topo: List[str], schedule: Dict[str, date], active: List[str]) -> bool:
        """Try to schedule submissions for the current round."""
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
        
        # Sort by priority weight
        ready = self._sort_by_priority(ready)
        
        # Try to schedule up to concurrency limit
        scheduled_this_round = False
        for sid in ready:
            if len(active) >= SCHEDULING_CONSTANTS.max_concurrent_submissions:
                break
            if not self._meets_deadline(self.submissions[sid], current):
                continue
            schedule[sid] = current
            active.append(sid)
            scheduled_this_round = True
        
        return scheduled_this_round
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight (inherited from GreedyScheduler)."""
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