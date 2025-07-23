~# TODO: Implementation Tasks

## Completed Tasks ✓

### 1. Blackout Period Support ✓
- [x] Add `blackout.json` to config loader
- [x] Create `is_working_day(date)` function
- [x] Update scheduler to skip weekends/holidays
- [x] Adjust duration calculations for blackout days

### 2. Priority Weighting System ✓
- [x] Load `priority_weights` from config.json
- [x] Apply weights in scheduling decisions
- [x] Sort ready items by weighted priority

### 3. Penalty Cost Implementation ✓
- [x] Use `penalty_cost_per_day` from mods.json
- [x] Add default penalties from config.json
- [x] Calculate cumulative delay costs

### 4. Early Abstract Scheduling ✓
- [x] Implement `abstract_advance_days` (30 days)
- [x] Schedule abstracts during slack periods
- [x] Add `enable_early_abstract_scheduling` flag

### 5. Core Config Updates ✓
- [x] Add `paper_parent_gap_days` to Config dataclass
- [x] Update scheduler to use config gap values
- [x] Load all new config sections

## Future Enhancements (Not Implemented)

### Conference Flexibility
- Dynamic reassignment near deadlines
- Track alternate conferences per paper
- Generate contingency recommendations

### Advanced Algorithm Features
- Stochastic exploration with priority perturbation
- 30-day lookahead heuristic
- Backtracking capability
- Critical path analysis

### Metrics and Reporting
- Solution quality metrics
- Local minima detection
- Historical pattern learning

## High Priority - Core Functionality

### 1. Blackout Period Support
- [ ] Add `blackout.json` to config loader
- [ ] Create `is_working_day(date)` function
- [ ] Update scheduler to skip weekends/holidays
- [ ] Adjust duration calculations for blackout days
- [ ] Test with 2025/2026 federal holidays

### 2. Priority Weighting System
- [ ] Load `priority_weights` from config.json
- [ ] Apply weights in scheduling decisions:
    - Engineering papers: 2.0
    - Medical papers: 1.0
    - Mods: 1.5
    - Abstracts: 0.5
- [ ] Sort ready items by weighted priority

### 3. Penalty Cost Implementation
- [ ] Use `penalty_cost_per_day` from mods.json
- [ ] Add default penalties from config.json
- [ ] Calculate cumulative delay costs
- [ ] Include in objective function
- [ ] Display total penalties in output

### 4. Early Abstract Scheduling
- [ ] Implement `abstract_advance_days` (30 days)
- [ ] Schedule abstracts during slack periods
- [ ] Ensure abstract → paper dependency respected
- [ ] Add `enable_early_abstract_scheduling` flag

## Medium Priority - Algorithm Enhancements

### 5. Lookahead Heuristic
- [ ] Create `evaluate_future_impact(item, date, days=30)`
- [ ] Score based on:
    - Future resource availability
    - Dependent item readiness
    - Deadline proximity
- [ ] Weight immediate vs future scores (0.5 factor)

### 6. Stochastic Exploration
- [ ] Add iteration counter to `greedy_schedule`
- [ ] Implement priority randomization:
    ```python
    noise = random.uniform(0.8, 1.2)
    priority = base_priority * noise
    ```
- [ ] Track best N solutions
- [ ] Bias toward successful patterns

### 7. Backtracking Capability
- [ ] Maintain decision history stack
- [ ] Implement `undo_last_n_decisions(n)`
- [ ] Trigger when utilization drops below 70%
- [ ] Limit backtrack depth to prevent thrashing

### 8. Critical Path Analysis
- [ ] Calculate total slack for each submission
- [ ] Identify zero-slack critical items
- [ ] Update slack dynamically during scheduling
- [ ] Prioritize critical path items

## Lower Priority - Additional Features

### 9. Conference Flexibility
- [ ] Track alternate conferences per paper
- [ ] Implement reassignment logic near deadlines
- [ ] Add `conference_response_time_days` (90)
- [ ] Generate contingency recommendations

### 10. Pause/Resume Support
- [ ] Add submission state tracking
- [ ] Allow partial progress recording
- [ ] Implement resume from checkpoint
- [ ] Handle interrupted submissions

### 11. Interactive Mode Improvements
- [ ] Show solution metrics after each generation
- [ ] Display improvement over previous
- [ ] Add 'B' key for best solution so far
- [ ] Show convergence indicators

### 12. Local Minima Detection
- [ ] Track utilization over time
- [ ] Monitor penalty accumulation rate
- [ ] Check critical path exhaustion
- [ ] Alert user when stuck

## Code Refactoring

### 13. Update Existing Functions

#### scheduler.py
- [ ] Replace hardcoded gaps with config values
- [ ] Add blackout day handling to date arithmetic
- [ ] Implement new objective function
- [ ] Add solution quality metrics

#### loader.py
- [ ] Load blackout.json
- [ ] Parse new config options
- [ ] Validate priority weights
- [ ] Handle penalty cost defaults

#### plots.py
- [ ] Show blackout periods on Gantt
- [ ] Color-code by priority weight
- [ ] Display penalty costs
- [ ] Add utilization chart

### 14. New Modules Needed

#### metrics.py
```python
def calculate_metrics(schedule, config):
    return {
        'makespan': ...,
        'utilization': ...,
        'total_penalties': ...,
        'front_loading_score': ...,
        'critical_path_slack': ...
    }
```

#### strategies.py
```python
def stochastic_greedy(config, n_iterations=100):
    # Multi-start randomized implementation

def lookahead_greedy(config, horizon_days=30):
    # Greedy with future impact evaluation
```

## Testing & Validation

### 15. Test Cases
- [ ] Blackout period boundary conditions
- [ ] Priority weight edge cases
- [ ] Backtracking convergence
- [ ] Conference reassignment scenarios
- [ ] Full 37-submission problem

### 16. Performance Benchmarks
- [ ] Measure schedule quality vs baseline
- [ ] Track algorithm runtime
- [ ] Monitor memory usage
- [ ] Validate optimality gap

## Documentation Updates

### 17. Update Documentation
- [ ] Add blackout.json format to README
- [ ] Document new config options
- [ ] Explain algorithm enhancements
- [ ] Add troubleshooting guide

### 18. Example Configurations
- [ ] Create example scenarios
- [ ] Provide tuning guidelines
- [ ] Document best practices
- [ ] Add performance tips
