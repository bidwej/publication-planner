"""Lookahead greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional, Set
from datetime import date, timedelta
from .greedy import GreedyScheduler
from .base import BaseScheduler
from ..models import Config, SubmissionType, Submission, SchedulerStrategy

@BaseScheduler.register_strategy(SchedulerStrategy.LOOKAHEAD)
class LookaheadGreedyScheduler(GreedyScheduler):
    """Lookahead greedy scheduler that considers future implications of decisions."""
    
    def __init__(self, config: Config, lookahead_days: int = 30):
        super().__init__(config)
        self.lookahead_days = lookahead_days
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight with lookahead consideration."""
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
            
            # Add lookahead bonus for submissions with dependencies
            lookahead_bonus = 0.0
            for other_sid in self.submissions:
                other_sub = self.submissions[other_sid]
                if sid in other_sub.depends_on:
                    # This submission blocks others, give it higher priority
                    lookahead_bonus += 0.5
            
            return base_priority + lookahead_bonus
        
        return sorted(ready, key=get_priority, reverse=True)
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline with lookahead buffer."""
        if not sub.conference_id or sub.conference_id not in self.conferences:
            return True
        
        conf = self.conferences[sub.conference_id]
        if sub.kind not in conf.deadlines:
            return True
        
        deadline = conf.deadlines[sub.kind]
        end_date = self._get_end_date(start, sub)
        
        # Add lookahead buffer to ensure we don't cut it too close
        buffer_date = deadline - timedelta(days=self.lookahead_days)
        return end_date <= buffer_date 