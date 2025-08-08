"""Heuristic scheduler implementation."""

from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta
from enum import Enum
from src.schedulers.base import BaseScheduler
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
        # Use shared setup
        schedule, topo, start_date, end_date = self._run_common_scheduling_setup()
        
        # Initialize active submissions list
        active: List[str] = []
        current_date = start_date
        
        while current_date <= end_date and len(schedule) < len(self.submissions):
            # Skip blackout dates
            if not self._is_working_day(current_date):
                current_date += timedelta(days=1)
                continue
            
            # Update active submissions
            active = self._update_active_submissions(active, schedule, current_date)
            
            # Get ready submissions
            ready = self._get_ready_submissions(topo, schedule, current_date)
            
            # Sort by heuristic strategy
            ready = self._sort_by_heuristic(ready)
            
            # Schedule submissions up to concurrency limit
            self._schedule_submissions_up_to_limit(ready, schedule, active, current_date)
            
            current_date += timedelta(days=1)
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
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
        def get_deadline(submission_id: str) -> date:
            submission = self.submissions[submission_id]
            if not submission.conference_id or submission.conference_id not in self.conferences:
                return date.max  # No deadline, schedule last
            conf = self.conferences[submission.conference_id]
            if submission.kind not in conf.deadlines:
                return date.max
            return conf.deadlines[submission.kind] or date.max
        
        return sorted(ready, key=get_deadline)
    
    def _sort_by_latest_start(self, ready: List[str]) -> List[str]:
        """Sort by latest start time first (reverse of earliest start)."""
        def get_latest_start(submission_id: str) -> date:
            submission = self.submissions[submission_id]
            if not submission.conference_id or submission.conference_id not in self.conferences:
                return date.min
            conf = self.conferences[submission.conference_id]
            if submission.kind not in conf.deadlines:
                return date.min
            deadline = conf.deadlines[submission.kind]
            if not deadline:
                return date.min
            # Calculate latest start that still meets deadline
            lead_time = self.config.min_paper_lead_time_days
            if submission.kind.value == "ABSTRACT":
                lead_time = self.config.min_abstract_lead_time_days
            return deadline - timedelta(days=lead_time)
        
        return sorted(ready, key=get_latest_start, reverse=True)
    
    def _sort_by_processing_time(self, ready: List[str], reverse: bool = False) -> List[str]:
        """Sort by processing time (shortest or longest first)."""
        def get_processing_time(submission_id: str) -> int:
            submission = self.submissions[submission_id]
            lead_time = self.config.min_paper_lead_time_days
            if submission.kind.value == "ABSTRACT":
                lead_time = self.config.min_abstract_lead_time_days
            return lead_time
        
        return sorted(ready, key=get_processing_time, reverse=reverse)
    
    def _sort_by_critical_path(self, ready: List[str]) -> List[str]:
        """Sort by critical path priority (submissions that block others get higher priority)."""
        def get_critical_priority(submission_id: str) -> int:
            # Count how many other submissions depend on this one
            blocking_count = 0
            for other_submission_id in self.submissions:
                other_submission = self.submissions[other_submission_id]
                if other_submission.depends_on and submission_id in other_submission.depends_on:
                    blocking_count += 1
            return blocking_count
        
        return sorted(ready, key=get_critical_priority, reverse=True)
