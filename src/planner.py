from __future__ import annotations
from typing import Dict, Union

from src.type import Config
from src.scheduler import greedy_schedule, integer_schedule


class Planner:
    """
    Convenience wrapper around the functional APIs in scheduler.py.
    Keeps backward-compat for code that expected a Planner class.
    """

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._greedy_cache: Dict[str, int] | None = None
        self._lp_cache: Dict[str, int] | None = None

    def greedy(self) -> Dict[str, int]:
        if self._greedy_cache is None:
            self._greedy_cache = greedy_schedule(self.cfg)
        return self._greedy_cache

    def lp_relaxation(self) -> Dict[str, int]:
        if self._lp_cache is None:
            self._lp_cache = integer_schedule(self.cfg)
        return self._lp_cache

    # Convenience aliases for older code
    greedy_schedule  = greedy
    solve_lp_relaxed = lp_relaxation
