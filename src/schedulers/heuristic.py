"""Heuristic scheduler implementation."""

from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from enum import Enum
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS


class HeuristicStrategy(Enum):
    """Different heuristic strategies for scheduling."""
    EARLIEST_DEADLINE = "earliest_deadline"
    LATEST_START = "latest_start"
    SHORTEST_PROCESSING_TIME = "shortest_processing_time"
    LONGEST_PROCESSING_TIME = "longest_processing_time"
    CRITICAL_PATH = "critical_path"


@BaseScheduler.register_strategy(SchedulerStrategy.HEURISTIC)
class HeuristicScheduler(BaseScheduler):
    """Heuristic scheduler that implements different scheduling strategies."""
    
    def __init__(self, config, strategy: HeuristicStrategy = HeuristicStrategy.EARLIEST_DEADLINE):
        """Initialize scheduler with config and strategy."""
        super().__init__(config)
        self.strategy = strategy
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule using the specified heuristic strategy.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        self._auto_link_abstract_paper()
        from src.validation.venue import _validate_venue_compatibility
        _validate_venue_compatibility(self.submissions, self.conferences)
        topo = self._topological_order()
        
        # Global time window - use robust date calculation
        current, end = self._get_scheduling_window()
        
        schedule: Dict[str, date] = {}
        active: List[str] = []
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", SCHEDULING_CONSTANTS.abstract_advance_days)
            self._schedule_early_abstracts(schedule, abstract_advance)
        
        while current <= end and len(schedule) < len(self.submissions):
            # Skip blackout dates
            if not is_working_day(current, self.config.blackout_dates):
                current += timedelta(days=1)
                continue
            
            # Retire finished drafts
            active = [
                sid for sid in active
                if self._get_end_date(schedule[sid], self.submissions[sid]) > current
            ]
            
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
            
            # Sort by heuristic strategy
            ready = self._sort_by_heuristic(ready)
            
            # Try to schedule up to concurrency limit
            for sid in ready:
                if len(active) >= SCHEDULING_CONSTANTS.max_concurrent_submissions:
                    break
                
                # Use comprehensive constraint validation
                if not self._validate_all_constraints(self.submissions[sid], current, schedule):
                    continue
                
                schedule[sid] = current
                active.append(sid)
            
            current += timedelta(days=1)
        
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            print("Note: Could not schedule %s submissions: %s", len(missing), missing)
            print("Successfully scheduled %s out of %s submissions", len(schedule), len(self.submissions))
        
        return schedule
    
    def _sort_by_heuristic(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by the specified heuristic strategy."""
        if self.strategy == HeuristicStrategy.EARLIEST_DEADLINE:
            return self._sort_by_earliest_deadline(ready)
        if self.strategy == HeuristicStrategy.LATEST_START:
            return self._sort_by_latest_start(ready)
        if self.strategy == HeuristicStrategy.SHORTEST_PROCESSING_TIME:
            return self._sort_by_processing_time(ready, reverse=False)
        if self.strategy == HeuristicStrategy.LONGEST_PROCESSING_TIME:
            return self._sort_by_processing_time(ready, reverse=True)
        if self.strategy == HeuristicStrategy.CRITICAL_PATH:
            return self._sort_by_critical_path(ready)
        raise ValueError(f"Unknown heuristic strategy: {self.strategy}")
    
    def _sort_by_earliest_deadline(self, ready: List[str]) -> List[str]:
        """Sort by earliest deadline first."""
        def get_deadline(sid: str) -> date:
            s = self.submissions[sid]
            if not s.conference_id or s.conference_id not in self.conferences:
                return date.max  # No deadline, schedule last
            conf = self.conferences[s.conference_id]
            if s.kind not in conf.deadlines:
                return date.max
            return conf.deadlines[s.kind] or date.max
        
        return sorted(ready, key=get_deadline)
    
    def _sort_by_latest_start(self, ready: List[str]) -> List[str]:
        """Sort by latest start time first (reverse of earliest start)."""
        def get_latest_start(sid: str) -> date:
            s = self.submissions[sid]
            if not s.conference_id or s.conference_id not in self.conferences:
                return date.min
            conf = self.conferences[s.conference_id]
            if s.kind not in conf.deadlines:
                return date.min
            deadline = conf.deadlines[s.kind]
            if not deadline:
                return date.min
            # Calculate latest start that still meets deadline
            lead_time = SCHEDULING_CONSTANTS.min_paper_lead_time_days
            if s.kind.value == "ABSTRACT":
                lead_time = SCHEDULING_CONSTANTS.min_abstract_lead_time_days
            return deadline - timedelta(days=lead_time)
        
        return sorted(ready, key=get_latest_start, reverse=True)
    
    def _sort_by_processing_time(self, ready: List[str], reverse: bool = False) -> List[str]:
        """Sort by processing time (shortest or longest first)."""
        def get_processing_time(sid: str) -> int:
            s = self.submissions[sid]
            lead_time = SCHEDULING_CONSTANTS.min_paper_lead_time_days
            if s.kind.value == "ABSTRACT":
                lead_time = SCHEDULING_CONSTANTS.min_abstract_lead_time_days
            return lead_time
        
        return sorted(ready, key=get_processing_time, reverse=reverse)
    
    def _sort_by_critical_path(self, ready: List[str]) -> List[str]:
        """Sort by critical path priority (submissions that block others get higher priority)."""
        def get_critical_priority(sid: str) -> int:
            # Count how many other submissions depend on this one
            blocking_count = 0
            for other_sid in self.submissions:
                other_sub = self.submissions[other_sid]
                if other_sub.depends_on and sid in other_sub.depends_on:
                    blocking_count += 1
            return blocking_count
        
        return sorted(ready, key=get_critical_priority, reverse=True)
