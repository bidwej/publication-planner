"""Stochastic scheduler implementation."""

from __future__ import annotations
import random
from typing import List
from schedulers.greedy import GreedyScheduler
from core.models import Submission
from core.constants import EFFICIENCY_CONSTANTS


class StochasticGreedyScheduler(GreedyScheduler):
    """Stochastic scheduler that adds randomness to priority selection."""
    
    # ===== INITIALIZATION =====
    
    def __init__(self, config, randomness_factor: float = EFFICIENCY_CONSTANTS.randomness_factor) -> None:
        """Initialize scheduler with config and randomness factor."""
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    # ===== OVERRIDDEN METHODS =====
    
    def get_priority(self, submission: Submission) -> float:
        """Override priority calculation to add randomness."""
        base_priority = super().get_priority(submission)
        
        # Add random noise to help escape local optima
        noise = random.uniform(-self.randomness_factor, self.randomness_factor)
        return base_priority + noise 
