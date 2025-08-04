# Paper Planner - Refactored Structure

This document describes the refactored modular structure of the Paper Planner system.

## New Directory Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── types.py          # Data structures (Config, Submission, Conference)
│   └── config.py         # Configuration loading and date/time utilities
├── schedulers/
│   ├── __init__.py
│   ├── base.py           # Abstract base scheduler
│   ├── greedy.py         # Basic greedy scheduler
│   ├── stochastic.py     # Stochastic greedy with randomness
│   ├── lookahead.py      # Lookahead greedy with future consideration
│   └── backtracking.py   # Backtracking greedy with undo capability
├── metrics/
│   ├── __init__.py
│   ├── makespan.py       # Makespan calculations
│   ├── utilization.py    # Resource utilization metrics
│   ├── penalties.py      # Penalty cost calculations
│   ├── deadlines.py      # Deadline compliance metrics
│   └── quality.py        # Quality metrics (front-loading, slack, etc.)
├── output/
│   ├── __init__.py
│   ├── tables.py         # Table generation
│   ├── plots.py          # Plot generation
│   └── console.py        # Console output formatting
└── planner.py            # Simple facade for backward compatibility
```

## Key Improvements

### 1. Modular Architecture
- **Separation of Concerns**: Each module has a specific responsibility
- **Extensibility**: Easy to add new schedulers, metrics, or output formats
- **Testability**: Each component can be tested independently

### 2. Multiple Scheduler Algorithms
- **GreedyScheduler**: Basic greedy algorithm with priority weighting
- **StochasticGreedyScheduler**: Adds randomness to break ties
- **LookaheadGreedyScheduler**: Considers future implications
- **BacktrackingGreedyScheduler**: Can undo decisions when stuck

### 3. Comprehensive Metrics
- **Makespan Analysis**: Total schedule duration and breakdowns
- **Resource Utilization**: Peak periods, idle time, efficiency
- **Penalty Calculations**: Deadline violations and dependency costs
- **Quality Metrics**: Front-loading, slack distribution, workload balance

### 4. Rich Output Options
- **Tables**: Summary tables, deadline tables, monthly views
- **Plots**: Gantt charts, utilization charts, deadline compliance
- **Console**: Formatted text output for quick analysis

## Usage Examples

### Basic Usage
```python
from core.config import load_config
from schedulers.greedy import GreedyScheduler
from output.console import print_schedule_summary

# Load configuration
config = load_config("data/config.json")

# Create scheduler
scheduler = GreedyScheduler(config)

# Generate schedule
schedule = scheduler.schedule()

# Print summary
print_schedule_summary(schedule, config)
```

### Comparing Schedulers
```python
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from metrics.quality import calculate_schedule_quality_score

schedulers = {
    "greedy": GreedyScheduler(config),
    "stochastic": StochasticGreedyScheduler(config)
}

results = {}
for name, scheduler in schedulers.items():
    schedule = scheduler.schedule()
    quality = calculate_schedule_quality_score(schedule, config)
    results[name] = quality

print(f"Best scheduler: {max(results, key=results.get)}")
```

### Generating Output
```python
from output.tables import generate_schedule_summary_table
from output.plots import plot_schedule
from output.console import print_metrics_summary

# Generate tables
summary_table = generate_schedule_summary_table(schedule, config)

# Generate plots
plot_schedule(schedule, config.submissions, save_path="schedule.png")

# Print metrics
print_metrics_summary(schedule, config)
```

## Backward Compatibility

The refactored system maintains backward compatibility through the `planner.py` facade:

```python
from planner import Planner

# Old-style usage still works
planner = Planner("data/config.json")
mod_sched, paper_sched = planner.schedule("greedy")
```

## Key Features

### Schedulers
- **BaseScheduler**: Abstract base class with common functionality
- **GreedyScheduler**: Priority-weighted greedy algorithm
- **StochasticGreedyScheduler**: Adds randomness for exploration
- **LookaheadGreedyScheduler**: Considers future dependencies
- **BacktrackingGreedyScheduler**: Can undo decisions

### Metrics
- **Makespan**: Total duration and parallel makespan
- **Utilization**: Resource usage patterns and efficiency
- **Penalties**: Deadline violations and dependency costs
- **Deadlines**: Compliance rates and risk assessment
- **Quality**: Overall schedule quality scores

### Output
- **Tables**: Structured data for analysis
- **Plots**: Visual representations of schedules
- **Console**: Formatted text output

## Benefits of Refactoring

1. **Maintainability**: Clear separation of concerns
2. **Extensibility**: Easy to add new algorithms or metrics
3. **Testability**: Each component can be tested independently
4. **Reusability**: Components can be used in different combinations
5. **Documentation**: Clear structure makes the codebase self-documenting

## Migration Guide

### For Existing Code
1. Update imports to use new module structure
2. Replace direct function calls with scheduler objects
3. Use the new metrics modules for analysis
4. Leverage the output modules for visualization

### For New Features
1. Add new schedulers by extending `BaseScheduler`
2. Create new metrics in the `metrics/` directory
3. Add output formats in the `output/` directory
4. Update the facade in `planner.py` if needed

## Example Script

Run `example_usage.py` to see the refactored system in action:

```bash
python example_usage.py
```

This will demonstrate all schedulers, metrics, and output formats. 