# Scheduler Architecture

## Overview

The scheduler architecture has been refactored to provide a clear separation between different scheduling approaches. The previous architecture was confusing because the base scheduler was already greedy, making it unclear what different schedulers actually did.

## New Architecture

### Base Scheduler (`BaseScheduler`)
- **Abstract base class** that defines the interface for all schedulers
- Provides common utility methods for dependency checking, deadline validation, etc.
- Cannot be instantiated directly (abstract class)

### Core Schedulers

#### 1. Greedy Scheduler (`GreedyScheduler`)
- **Implements greedy algorithm**: schedules submissions as early as possible based on priority
- **Priority-based selection**: uses configurable weights for different submission types
- **Simple and fast**: good baseline for comparison

#### 2. Heuristic Scheduler (`HeuristicScheduler`)
- **Multiple strategies**: implements different scheduling heuristics
- **Strategies available**:
  - `EARLIEST_DEADLINE`: Schedule submissions with earliest deadlines first
  - `LATEST_START`: Schedule submissions that can start latest first
  - `SHORTEST_PROCESSING_TIME`: Schedule shortest tasks first
  - `LONGEST_PROCESSING_TIME`: Schedule longest tasks first
  - `CRITICAL_PATH`: Prioritize submissions that block others

#### 3. Optimal Scheduler (`OptimalScheduler`)
- **MILP optimization**: placeholder for mathematical optimization
- **Future implementation**: will use PuLP or OR-Tools
- **Multiple objectives**: minimize makespan, maximize quality, etc.

#### 4. Random Scheduler (`RandomScheduler`)
- **Baseline comparison**: schedules submissions in random order
- **Reproducible**: uses configurable seed for consistent results
- **Useful for**: testing and comparison with other algorithms

### Greedy Variants

These schedulers inherit from `GreedyScheduler` and add specific enhancements:

#### 1. Lookahead Greedy (`LookaheadGreedyScheduler`)
- **Future consideration**: adds lookahead buffer to deadline checking
- **Dependency awareness**: prioritizes submissions that block others
- **Configurable**: `lookahead_days` parameter

#### 2. Stochastic Greedy (`StochasticGreedyScheduler`)
- **Randomness**: adds random noise to priority calculations
- **Exploration**: helps avoid local optima
- **Configurable**: `randomness_factor` parameter

#### 3. Backtracking Greedy (`BacktrackingGreedyScheduler`)
- **Undo decisions**: can backtrack when stuck
- **Recovery**: removes recent decisions to try different paths
- **Configurable**: `max_backtracks` parameter

## Usage Examples

```python
from src.schedulers import (
    GreedyScheduler,
    HeuristicScheduler,
    HeuristicStrategy,
    OptimalScheduler,
    RandomScheduler
)

# Basic greedy scheduling
greedy = GreedyScheduler(config)
schedule = greedy.schedule()

# Heuristic scheduling with earliest deadline
heuristic = HeuristicScheduler(config, HeuristicStrategy.EARLIEST_DEADLINE)
schedule = heuristic.schedule()

# Random baseline
random_scheduler = RandomScheduler(config, seed=42)
schedule = random_scheduler.schedule()

# Optimal (placeholder for now)
optimal = OptimalScheduler(config, "minimize_makespan")
schedule = optimal.schedule()
```

## Benefits of New Architecture

1. **Clear separation**: Each scheduler has a distinct purpose
2. **Extensible**: Easy to add new schedulers by inheriting from base
3. **Testable**: Each scheduler can be tested independently
4. **Comparable**: Different approaches can be compared fairly
5. **Future-ready**: Placeholder for MILP optimization

## Migration from Old Architecture

The old architecture had:
- `BaseScheduler` (was actually greedy)
- `GreedyScheduler` (redundant)
- Various greedy variants

The new architecture has:
- `BaseScheduler` (truly abstract)
- `GreedyScheduler` (implements greedy algorithm)
- `HeuristicScheduler` (different heuristics)
- `OptimalScheduler` (for MILP optimization)
- `RandomScheduler` (for baseline comparison)
- Greedy variants (inherit from `GreedyScheduler`)

This provides a much clearer and more maintainable structure.
