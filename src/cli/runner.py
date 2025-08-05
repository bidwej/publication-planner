"""CLI execution logic for the paper planner."""

from ..models import SchedulerStrategy


def get_scheduler_strategy(scheduler_name: str) -> SchedulerStrategy:
    """Convert scheduler name to enum."""
    strategy_map = {
        "greedy": SchedulerStrategy.GREEDY,
        "stochastic": SchedulerStrategy.STOCHASTIC,
        "lookahead": SchedulerStrategy.LOOKAHEAD,
        "backtracking": SchedulerStrategy.BACKTRACKING
    }
    return strategy_map.get(scheduler_name, SchedulerStrategy.GREEDY) 