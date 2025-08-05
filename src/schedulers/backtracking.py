"""Backtracking greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional, Set
from datetime import date, timedelta
from .greedy import GreedyScheduler
from .base import BaseScheduler
from ..models import Config, SubmissionType, Submission, SchedulerStrategy
from ..dates import is_working_day
@BaseScheduler.register_strategy(SchedulerStrategy.BACKTRACKING)
class BacktrackingGreedyScheduler(GreedyScheduler):
    """Backtracking greedy scheduler that can undo decisions when stuck."""
    
    def __init__(self, config: Config, max_backtracks: int = 5):
        super().__init__(config)
        self.max_backtracks = max_backtracks
    
    # Explicitly declare inherited methods for linter
    def _deps_satisfied(self, sub: Submission, schedule: Dict[str, date], now: date) -> bool:
        """Check if all dependencies are satisfied."""
        return super()._deps_satisfied(sub, schedule, now)
    
    def _get_end_date(self, start_date: date, sub: Submission) -> date:
        """Calculate the end date for a submission."""
        return super()._get_end_date(start_date, sub)
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline."""
        return super()._meets_deadline(sub, start)
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight."""
        return super()._sort_by_priority(ready)
    
    def _schedule_early_abstracts(self, schedule: Dict[str, date], advance_days: int) -> None:
        """Schedule abstracts early if enabled."""
        return super()._schedule_early_abstracts(schedule, advance_days)
    
    def _auto_link_abstract_paper(self) -> None:
        """Automatically link abstracts to papers if they share the same conference."""
        return super()._auto_link_abstract_paper()
    
    def _validate_venue_compatibility(self) -> None:
        """Validate that submissions are compatible with their venues."""
        return super()._validate_venue_compatibility()
    
    def _topological_order(self) -> List[str]:
        """Generate topological order of submissions."""
        return super()._topological_order()
    
    def schedule(self) -> Dict[str, date]:
        """Generate schedule with backtracking capability."""
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
        backtracks = 0
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", 30)
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
            
            # Sort by priority weight
            ready = self._sort_by_priority(ready)
            
            # Try to schedule up to concurrency limit
            scheduled_this_round = False
            for sid in ready:
                if len(active) >= self.config.max_concurrent_submissions:
                    break
                if not self._meets_deadline(self.submissions[sid], current):
                    continue
                schedule[sid] = current
                active.add(sid)
                scheduled_this_round = True
            
            # If we couldn't schedule anything and we're not at the end, try backtracking
            if not scheduled_this_round and backtracks < self.max_backtracks:
                if self._backtrack(schedule, active, current):
                    backtracks += 1
                    continue
            
            current += timedelta(days=1)
        
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            raise RuntimeError(f"Could not schedule submissions: {missing}")
        
        return schedule
    
    def _backtrack(self, schedule: Dict[str, date], active: Set[str], current: date) -> bool:
        """Try to backtrack by removing a recent decision."""
        if not schedule:
            return False
        
        # Find the most recent submission that could be rescheduled
        recent_subs = [(sid, start_date) for sid, start_date in schedule.items() 
                       if start_date >= current - timedelta(days=7)]
        
        if not recent_subs:
            return False
        
        # Sort by start date (most recent first)
        recent_subs.sort(key=lambda x: x[1], reverse=True)
        
        # Try to remove the most recent submission
        for sid, start_date in recent_subs:
            sub = self.submissions[sid]
            
            # Check if removing this submission would help
            if self._can_reschedule_earlier(sid, schedule, current):
                del schedule[sid]
                if sid in active:
                    active.remove(sid)
                return True
        
        return False
    
    def _can_reschedule_earlier(self, sid: str, schedule: Dict[str, date], current: date) -> bool:
        """Check if a submission could be rescheduled earlier."""
        sub = self.submissions[sid]
        current_start = schedule[sid]
        
        # Try to find an earlier start date
        days_diff = (current_start - current).days
        for test_date in range(days_diff - 1, -1, -1):
            test_start = current + timedelta(days=test_date)
            if (is_working_day(test_start, self.config.blackout_dates) and 
                (not sub.earliest_start_date or test_start >= sub.earliest_start_date) and
                self._meets_deadline(sub, test_start)):
                return True
        
        return False 