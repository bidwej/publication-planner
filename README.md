# Paper Planner - Advanced Academic Scheduling System

A sophisticated constraint-based optimization framework for scheduling academic submissions (papers, abstracts, and modifications) with complex dependencies, deadline constraints, and resource limitations.

## 🚀 Features

### **Modular Architecture**
- **Core**: Data structures and configuration management
- **Schedulers**: Multiple scheduling algorithms (Greedy, Stochastic, Lookahead, Backtracking)
- **Metrics**: Comprehensive schedule analysis (Makespan, Utilization, Penalties, Deadlines, Quality)
- **Output**: Rich visualization and reporting (Tables, Plots, Console)

### **Advanced Scheduling Algorithms**
- **GreedyScheduler**: Priority-weighted greedy algorithm with blackout date handling
- **StochasticGreedyScheduler**: Adds randomness for exploration and tie-breaking
- **LookaheadGreedyScheduler**: Considers future implications and dependencies
- **BacktrackingGreedyScheduler**: Can undo decisions when stuck

### **Comprehensive Metrics**
- **Makespan Analysis**: Total duration, parallel makespan, breakdowns
- **Resource Utilization**: Peak periods, idle time, efficiency analysis
- **Penalty Calculations**: Deadline violations, dependency costs, earliness bonuses
- **Deadline Compliance**: Risk assessment, margin analysis, violation tracking
- **Quality Metrics**: Front-loading, slack distribution, workload balance

### **Rich Output Options**
- **Tables**: Summary tables, deadline tables, monthly views
- **Plots**: Gantt charts, utilization charts, deadline compliance
- **Console**: Formatted text output for quick analysis

## 📁 Project Structure

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

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd paper-planner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -m pytest tests/ -v
   ```

## 📖 Quick Start

### Basic Usage

```python
from core.config import load_config
from schedulers.greedy import GreedyScheduler
from output.console import print_schedule_summary

# Load configuration
config = load_config("config.json")

# Create scheduler
scheduler = GreedyScheduler(config)

# Generate schedule
schedule = scheduler.schedule()

# Print summary
print_schedule_summary(schedule, config)
```

### Comparing Multiple Schedulers

```python
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from metrics.quality import calculate_schedule_quality_score

# Test different schedulers
schedulers = {
    "Greedy": GreedyScheduler(config),
    "Stochastic": StochasticGreedyScheduler(config),
    "Lookahead": LookaheadGreedyScheduler(config)
}

results = {}
for name, scheduler in schedulers.items():
    schedule = scheduler.schedule()
    quality = calculate_schedule_quality_score(schedule, config)
    results[name] = quality
    print(f"{name}: Quality Score = {quality:.3f}")

best_scheduler = max(results, key=results.get)
print(f"Best scheduler: {best_scheduler}")
```

### Generating Rich Output

```python
from output.tables import generate_schedule_summary_table
from output.plots import plot_schedule
from output.console import print_metrics_summary

# Generate tables
summary_table = generate_schedule_summary_table(schedule, config)

# Generate plots
plot_schedule(schedule, config.submissions, save_path="schedule.png")

# Print comprehensive metrics
print_metrics_summary(schedule, config)
```

## ⚙️ Configuration

### Configuration File (config.json)

```json
{
  "min_abstract_lead_time_days": 0,
  "min_paper_lead_time_days": 60,
  "max_concurrent_submissions": 2,
  "default_paper_lead_time_months": 3,
  "priority_weights": {
    "engineering_paper": 2.0,
    "medical_paper": 1.0,
    "mod": 1.5,
    "abstract": 0.5
  },
  "penalty_costs": {
    "default_mod_penalty_per_day": 1000,
    "default_paper_penalty_per_day": 500
  },
  "scheduling_options": {
    "enable_early_abstract_scheduling": true,
    "abstract_advance_days": 30,
    "enable_blackout_periods": true
  },
  "data_files": {
    "conferences": "data/conferences.json",
    "mods": "data/mods.json",
    "papers": "data/papers.json",
    "blackouts": "data/blackout.json"
  }
}
```

### Data Files

#### conferences.json
```json
[
  {
    "name": "ICML",
    "conference_type": "ENGINEERING",
    "recurrence": "annual",
    "abstract_deadline": "2025-01-23",
    "full_paper_deadline": "2025-01-30"
  }
]
```

#### papers.json
```json
[
  {
    "id": "J1",
    "title": "Computer Vision (CV) endoscopy review",
    "earliest_start_date": "2025-01-01",
    "conference_id": "ICML",
    "engineering": true,
    "mod_dependencies": [1],
    "parent_papers": [],
    "lead_time_from_parents": 0,
    "draft_window_months": 2
  }
]
```

## 🔧 Advanced Usage

### Custom Scheduler Configuration

```python
from schedulers.stochastic import StochasticGreedyScheduler

# Configure stochastic scheduler with custom randomness
scheduler = StochasticGreedyScheduler(
    config, 
    randomness_factor=0.2  # Increase randomness
)
```

### Detailed Metrics Analysis

```python
from metrics.makespan import calculate_makespan, get_makespan_breakdown
from metrics.utilization import calculate_resource_utilization
from metrics.penalties import calculate_penalty_costs
from metrics.deadlines import calculate_deadline_compliance
from metrics.quality import calculate_schedule_quality_score

# Comprehensive analysis
makespan = calculate_makespan(schedule, config)
utilization = calculate_resource_utilization(schedule, config)
penalties = calculate_penalty_costs(schedule, config)
compliance = calculate_deadline_compliance(schedule, config)
quality = calculate_schedule_quality_score(schedule, config)

print(f"Makespan: {makespan} days")
print(f"Avg Utilization: {utilization['avg_utilization']:.1%}")
print(f"Total Penalties: ${penalties['total_penalty']:.2f}")
print(f"Deadline Compliance: {compliance['compliance_rate']:.1f}%")
print(f"Quality Score: {quality:.3f}")
```

### Backward Compatibility

The system maintains backward compatibility through the `planner.py` facade:

```python
from planner import Planner

# Old-style usage still works
planner = Planner("config.json")
mod_sched, paper_sched = planner.schedule("greedy")
```

## 📊 Performance Characteristics

### Typical Results (37-submission problem)
- **Schedule Generation**: <1 second
- **Solution Variants**: 100+ unique schedules
- **Optimality Gap**: ~10-20% vs theoretical lower bound
- **Makespan**: 18-24 months depending on constraints

### Algorithm Performance Comparison
| Scheduler | Makespan (days) | Utilization | Quality Score |
|-----------|-----------------|-------------|---------------|
| Greedy | 764 | 81.4% | 0.544 |
| Stochastic | 772 | 89.5% | 0.569 |
| Lookahead | 795 | 83.4% | 0.550 |
| Backtracking | Failed | - | - |

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Test Coverage
- **Unit Tests**: 9 comprehensive tests
- **Edge Cases**: Biennial conferences, concurrency limits, parent-child relationships
- **Integration Tests**: Full workflow validation
- **Backward Compatibility**: Legacy interface testing

### Test Categories
- `test_validate_config_runs`: Configuration validation
- `test_abstract_before_full_each_year`: Abstract/paper sequencing
- `test_biennial_iccv`: Biennial conference handling
- `test_concurrency_limit`: Resource constraint validation
- `test_mod_paper_alignment`: Modification/paper dependencies
- `test_parent_child_lead`: Parent-child relationship timing
- `test_multi_parent`: Complex dependency graphs
- `test_free_slack`: Slack time analysis
- `test_biennial_conference`: Conference recurrence patterns

## 🔍 Metrics Explained

### Makespan Analysis
- **Total Duration**: Complete schedule timeline
- **Parallel Makespan**: Optimal parallel execution time
- **Breakdown**: Detailed time allocation per submission type

### Resource Utilization
- **Average Utilization**: Overall resource efficiency
- **Peak Periods**: High-activity time windows
- **Idle Time**: Underutilized periods
- **Efficiency**: Resource optimization metrics

### Penalty Calculations
- **Deadline Violations**: Late submission costs
- **Dependency Costs**: Violation of dependency constraints
- **Earliness Bonuses**: Rewards for early completion
- **Total Penalty**: Comprehensive cost assessment

### Deadline Compliance
- **Compliance Rate**: Percentage of on-time submissions
- **Risk Assessment**: Probability of deadline violations
- **Margin Analysis**: Buffer time before deadlines
- **Violation Tracking**: Detailed late submission analysis

### Quality Metrics
- **Front-loading Score**: Early work distribution
- **Slack Distribution**: Buffer time allocation
- **Workload Balance**: Even resource distribution
- **Dependency Satisfaction**: Constraint compliance

## 🎯 Use Cases

### Academic Research Planning
- Schedule multiple paper submissions across conferences
- Manage complex dependency relationships
- Optimize for early completion and quality

### Medical Device Development
- Coordinate FDA regulatory submissions
- Align with clinical trial timelines
- Balance engineering and medical publications

### Conference Strategy
- Plan submissions across multiple venues
- Handle biennial vs annual conferences
- Optimize for acceptance probability

### Resource Management
- Balance concurrent project capacity
- Respect work-life boundaries (weekends, holidays)
- Optimize team utilization

## 🚀 Future Enhancements

### Conference Acceptance Modeling
- Track historical acceptance rates by venue/topic
- Model as probability distributions
- Submit to multiple conferences with overlapping deadlines
- Contingency planning for rejections

### Advanced Optimization
- Constraint programming with OR-Tools
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

## 📚 API Reference

### Core Classes

#### Config
```python
@dataclass
class Config:
    min_abstract_lead_time_days: int
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    default_paper_lead_time_months: int
    conferences: List[Conference]
    submissions: List[Submission]
    data_files: Dict[str, str]
    priority_weights: Optional[Dict[str, float]]
    penalty_costs: Optional[Dict[str, float]]
    scheduling_options: Optional[Dict[str, Any]]
    blackout_dates: Optional[List[date]]
```

#### Submission
```python
@dataclass
class Submission:
    id: str
    kind: SubmissionType  # ABSTRACT or PAPER
    title: str
    earliest_start_date: date
    conference_id: Optional[str]
    engineering: bool
    depends_on: List[str]
    penalty_cost_per_day: float
    lead_time_from_parents: int
    draft_window_months: int
```

### Scheduler Interface

```python
class BaseScheduler(ABC):
    def schedule(self) -> Dict[str, date]:
        """Generate a schedule for all submissions."""
        pass
    
    def validate_schedule(self, schedule: Dict[str, date]) -> bool:
        """Validate that a schedule meets all constraints."""
        pass
    
    def get_schedule_metrics(self, schedule: Dict[str, date]) -> Dict[str, float]:
        """Calculate metrics for a given schedule."""
        pass
```

### Metrics Functions

```python
# Makespan
calculate_makespan(schedule: Dict[str, date], config: Config) -> int
get_makespan_breakdown(schedule: Dict[str, date], config: Config) -> Dict

# Utilization
calculate_resource_utilization(schedule: Dict[str, date], config: Config) -> Dict[str, float]
calculate_peak_utilization_periods(schedule: Dict[str, date], config: Config) -> List[Dict]

# Penalties
calculate_penalty_costs(schedule: Dict[str, date], config: Config) -> Dict[str, float]
get_penalty_breakdown(schedule: Dict[str, date], config: Config) -> Dict

# Deadlines
calculate_deadline_compliance(schedule: Dict[str, date], config: Config) -> Dict[str, float]
get_deadline_violations(schedule: Dict[str, date], config: Config) -> List[Dict]

# Quality
calculate_schedule_quality_score(schedule: Dict[str, date], config: Config) -> float
calculate_front_loading_score(schedule: Dict[str, date], config: Config) -> float
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-scheduler`
3. **Add tests**: Ensure all new functionality is tested
4. **Run tests**: `python -m pytest tests/ -v`
5. **Submit pull request**: Include comprehensive documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Edward McCoul, MD**: For the original problem specification and domain expertise
- **Academic Community**: For feedback on scheduling algorithms and metrics
- **Open Source Contributors**: For the underlying libraries and tools

---

**Paper Planner** - Advanced academic scheduling with constraint-based optimization