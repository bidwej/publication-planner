## Limitations

- No true global optimization (NP-hard problem)
- Single-machine model (no parallel authoring)
- Deterministic durations (no stochastic modeling)
- No partial progress tracking

## Performance

Typical results on 37-submission problem:
- Schedule generation: <1 second
- Solution variants: 100+ unique schedules  
- Optimality gap: ~10-20% vs theoretical lower bound
- Makespan: 18-24 months depending on constraints

## Future Work

### Conference Acceptance Modeling
Track historical acceptance rates by venue/topic:
- Model as probability distributions
- Submit to multiple conferences with overlapping deadlines
- Contingency planning for rejections


### Advanced Optimization
- Constraint programming with OR-Tools (pure Python)
- Monte Carlo tree search for solution exploration
- Reinforcement learning from historical schedules
- Robust optimization with uncertainty sets

### Quality vs Speed Tradeoffs
- Model review cycles and revision quality
- Rush penalties for compressed timelines
- Author bandwidth constraints
- Optimal draft iteration counts

### Dynamic Rescheduling
- Monitor actual vs planned progress
- Trigger replanning on delays >7 days
- Maintain solution pool for quick pivots