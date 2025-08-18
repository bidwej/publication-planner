"""Stochastic greedy scheduler implementation."""

from __future__ import annotations
import random
from typing import List
from schedulers.greedy import GreedyScheduler
from schedulers.base import BaseScheduler
from core.models import SchedulerStrategy
from core.constants import EFFICIENCY_CONSTANTS


class StochasticGreedyScheduler(GreedyScheduler):
    """Stochastic greedy scheduler that adds randomness to priority selection."""
    
    def __init__(self, config, randomness_factor: float = EFFICIENCY_CONSTANTS.randomness_factor):
        """Initialize scheduler with config and randomness factor."""
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Override priority selection to add randomness."""
        def get_priority(submission_id: str) -> float:
            submission = self.submissions[submission_id]
            base_priority = self._get_base_priority(submission)
            
            # Add random noise
            noise = random.uniform(-self.randomness_factor, self.randomness_factor)
            return base_priority + noise
        
        return sorted(ready, key=get_priority, reverse=True) 
