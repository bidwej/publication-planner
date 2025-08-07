"""Stochastic greedy scheduler implementation."""

from __future__ import annotations
import random
from typing import List
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.base import BaseScheduler
from src.core.models import SchedulerStrategy
from src.core.constants import SCHEDULING_CONSTANTS



@BaseScheduler.register_strategy(SchedulerStrategy.STOCHASTIC)
class StochasticGreedyScheduler(GreedyScheduler):
    """Stochastic greedy scheduler that adds randomness to priority selection."""
    
    def __init__(self, config, randomness_factor: float = SCHEDULING_CONSTANTS.randomness_factor):
        """Initialize scheduler with config and randomness factor."""
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Override priority selection to add randomness."""
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
            
            # Add random noise
            noise = random.uniform(-self.randomness_factor, self.randomness_factor)
            return base_priority + noise
        
        return sorted(ready, key=get_priority, reverse=True) 