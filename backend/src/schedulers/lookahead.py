"""Lookahead greedy scheduler implementation."""

from __future__ import annotations
from typing import List
from datetime import timedelta, date
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.base import BaseScheduler
from src.core.models import Submission, SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS


class LookaheadGreedyScheduler(GreedyScheduler):
    """Lookahead greedy scheduler that considers future implications of decisions."""
    
    def __init__(self, config, lookahead_days: int = SCHEDULING_CONSTANTS.lookahead_window_days):
        """Initialize scheduler with config and lookahead buffer."""
        super().__init__(config)
        self.lookahead_days = lookahead_days
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Override priority selection to add lookahead consideration."""
        def get_priority(submission_id: str) -> float:
            submission = self.submissions[submission_id]
            base_priority = self._get_base_priority(submission)
            
            # Add lookahead bonus for submissions with dependencies
            lookahead_bonus = 0.0
            for other_submission_id in self.submissions:
                other_submission = self.submissions[other_submission_id]
                if other_submission.depends_on and submission_id in other_submission.depends_on:
                    # This submission blocks others, give it higher priority
                    lookahead_bonus += EFFICIENCY_CONSTANTS.lookahead_bonus_increment
            
            return base_priority + lookahead_bonus
        
        return sorted(ready, key=get_priority, reverse=True)
    
    def _meets_deadline(self, submission: Submission, start_date: date) -> bool:
        """Override deadline checking to add lookahead buffer."""
        if not submission.conference_id or submission.conference_id not in self.conferences:
            return True
        
        conf = self.conferences[submission.conference_id]
        if submission.kind not in conf.deadlines:
            return True
        
        deadline = conf.deadlines[submission.kind]
        if deadline is None:
            return True
        
        end_date = self._get_end_date(start_date, submission)
        
        # Add lookahead buffer to ensure we don't cut it too close
        buffer_date = deadline - timedelta(days=self.lookahead_days)
        return end_date <= buffer_date 
