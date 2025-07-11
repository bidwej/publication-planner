from __future__ import annotations
from typing import Dict, Optional
from datetime import date

from src.type import Config
from src.scheduler import greedy_schedule


class Planner:
    """
    Convenience wrapper around the functional APIs in scheduler.py.
    Keeps backward-compat for code that expected a Planner class.
    """

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._greedy_cache: Optional[Dict[str, date]] = None

    def greedy(self) -> Dict[str, date]:
        if self._greedy_cache is None:
            self._greedy_cache = greedy_schedule(self.cfg)
        return self._greedy_cache

    def lp_relaxation(self) -> Dict[str, date]:
        # LP solver not implemented - falls back to greedy
        return self.greedy()

    # Convenience aliases for older code
    greedy_schedule = greedy
    solve_lp_relaxed = lp_relaxation
