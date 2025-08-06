"""Greedy scheduler implementation using inheritance from BaseScheduler."""

from .base import BaseScheduler


class GreedyScheduler(BaseScheduler):
    """Greedy daily scheduler for abstracts & papers with priority weighting and blackout date handling."""
    
    # Inherits everything from BaseScheduler - no overrides needed
    # The base implementation is already greedy
    pass 