"""Lookahead greedy scheduler implementation."""

from __future__ import annotations
from typing import List
from datetime import timedelta, date
from schedulers.greedy import GreedyScheduler
from core.models import Submission, Schedule
from core.constants import SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS


class LookaheadScheduler(GreedyScheduler):
    """Lookahead greedy scheduler that considers future implications of decisions."""
    
    def __init__(self, config, lookahead_days: int = SCHEDULING_CONSTANTS.lookahead_window_days) -> None:
        """Initialize scheduler with config and lookahead buffer.
        
        Args:
            config: Configuration object containing submissions, conferences, and settings
            lookahead_days: Number of days to look ahead for deadline buffer
        """
        super().__init__(config)
        self.lookahead_days = lookahead_days
    
    def get_priority(self, submission: Submission) -> float:
        """Override priority calculation to add lookahead consideration.
        
        Args:
            submission: Submission to calculate priority for
            
        Returns:
            Priority score with lookahead bonus for blocking submissions (higher = more important)
        """
        base_priority = super().get_priority(submission)
        
        # Add lookahead bonus for submissions with dependencies
        lookahead_bonus = 0.0
        for other_submission_id in self.submissions:
            other_submission = self.submissions[other_submission_id]
            if other_submission.depends_on and submission.id in other_submission.depends_on:
                # This submission blocks others, give it higher priority
                lookahead_bonus += EFFICIENCY_CONSTANTS.lookahead_bonus_increment
        
        return base_priority + lookahead_bonus
    
    def can_schedule(self, submission: Submission, start_date: date, schedule: Schedule) -> bool:
        """Override scheduling validation to add lookahead buffer for deadlines.
        
        Args:
            submission: Submission to validate
            start_date: Proposed start date
            schedule: Current schedule
            
        Returns:
            True if submission can be scheduled with lookahead buffer, False otherwise
        """
        # First check base constraints
        if not super().can_schedule(submission, start_date, schedule):
            return False
        
        # Add lookahead deadline checking
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
