"""Stochastic greedy scheduler implementation."""

from __future__ import annotations
import random
from typing import List
from schedulers.greedy import GreedyScheduler
from core.models import Submission
from core.constants import EFFICIENCY_CONSTANTS


class StochasticScheduler(GreedyScheduler):
    """Stochastic greedy scheduler that adds randomness to priority selection."""
    
    def __init__(self, config, randomness_factor: float = EFFICIENCY_CONSTANTS.randomness_factor) -> None:
        """Initialize scheduler with config and randomness factor.
        
        Args:
            config: Configuration object containing submissions, conferences, and settings
            randomness_factor: Factor controlling the amount of random noise added to priorities
        """
        super().__init__(config)
        self.randomness_factor = randomness_factor
    
    def get_priority(self, submission: Submission) -> float:
        """Override priority calculation to add randomness.
        
        Args:
            submission: Submission to calculate priority for
            
        Returns:
            Priority score with random noise added (higher = more important)
        """
        base_priority = super().get_priority(submission)
        
        # Add random noise
        noise = random.uniform(-self.randomness_factor, self.randomness_factor)
        return base_priority + noise 
