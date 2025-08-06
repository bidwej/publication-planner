"""Stochastic greedy scheduler implementation."""

from __future__ import annotations
import random
from typing import Dict, List, Optional, Set
from datetime import date, timedelta
from .greedy import GreedyScheduler
from .base import BaseScheduler
from core.models import Config, SchedulerStrategy

@BaseScheduler.register_strategy(SchedulerStrategy.STOCHASTIC)
class StochasticGreedyScheduler(GreedyScheduler):
    """Stochastic greedy scheduler that adds randomness to priority selection."""
    
    def __init__(self, config: Config, randomness_factor: float = 0.1):
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight with added randomness."""
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