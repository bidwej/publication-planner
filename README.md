# Paper Planner - Advanced Academic Scheduling System

A sophisticated constraint-based optimization framework for scheduling academic submissions (papers, abstracts, and modifications) with complex dependencies, deadline constraints, and resource limitations.

## 🎯 Purpose

This system was specifically designed for **EndoscopeAI**, a medical device development project requiring coordination between:
- **17 PCCP (Predetermined Change Control Plans) modifications** for FDA regulatory submissions
- **20+ scientific papers** for academic publication
- **14 major conferences** with strict deadlines
- **Complex dependencies** between modifications, papers, and conferences

The system ensures regulatory compliance while optimizing for early completion, resource utilization, and conference deadline compliance.

## 🚀 Features

### **Modular Architecture**
- **Core**: Data structures, configuration management, and centralized date utilities
- **Schedulers**: Multiple scheduling algorithms (Greedy, Stochastic, Lookahead, Backtracking)
- **Metrics**: Comprehensive schedule analysis (Makespan, Utilization, Penalties, Deadlines, Quality)
- **Output**: Rich visualization and reporting (Tables, Plots, Console)

### **Advanced Scheduling Algorithms**
- **GreedyScheduler**: Priority-weighted greedy algorithm with blackout date handling
- **StochasticGreedyScheduler**: Adds randomness for exploration and tie-breaking
- **LookaheadGreedyScheduler**: Considers future implications and dependencies (30-day lookahead)
- **BacktrackingGreedyScheduler**: Can undo decisions when stuck

### **Comprehensive Metrics**
- **Makespan Analysis**: Total duration, parallel makespan, breakdowns
- **Resource Utilization**: Peak periods, idle time, efficiency analysis
- **Penalty Calculations**: Deadline violations, dependency costs, earliness bonuses
- **Deadline Compliance**: Risk assessment, margin analysis, violation tracking
- **Quality Metrics**: Front-loading, slack distribution, workload balance
- **Solution Quality Metrics**: Critical path analysis and slack calculation

### **Rich Output Options**
- **Tables**: Summary tables, deadline tables, monthly views
- **Plots**: Gantt charts, utilization charts, deadline compliance
- **Console**: Formatted text output for quick analysis

### **Advanced Constraint Handling**
- **Soft Block Model**: PCCP modifications can slip ±2 months with penalties
- **Concurrency Control**: Maintains 1-2 papers in drafting pipeline
- **Conference Compatibility**: Ensures papers match appropriate venues
- **Dependency Satisfaction**: Respects complex paper-to-paper and mod-to-paper relationships
- **Early Abstract Scheduling**: Abstracts can be scheduled 30 days in advance
- **Priority Weighting**: Engineering papers (2.0), Medical papers (1.0), Mods (1.5), Abstracts (0.5)
- **Single-Conference Policy**: Each paper submitted to one venue per annual cycle
- **Mod-to-Mod Dependencies**: Specific technical dependencies (Mod 3→4, Mod 4→5)

## 📁 Project Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── types.py          # Data structures (Config, Submission, Conference)
│   ├── config.py         # Configuration loading
│   └── dates.py          # Centralized date parsing and utilities
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

### **Modular Architecture Benefits**
- **Separation of Concerns**: Each module has a specific responsibility
- **Extensibility**: Easy to add new schedulers, metrics, or output formats
- **Testability**: Each component can be tested independently
- **Maintainability**: Clear boundaries between different system components

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

### Command Line Interface

The `generate_schedule.py` script provides a powerful CLI with multiple modes:

```bash
# Interactive mode (default) - generate and visualize schedules
python generate_schedule.py

# Compare all schedulers and show performance metrics
python generate_schedule.py --mode compare

# Detailed analysis with specific scheduler
python generate_schedule.py --mode analyze --scheduler greedy

# Use different scheduler in interactive mode
python generate_schedule.py --scheduler backtracking

# Custom configuration and date ranges
python generate_schedule.py --config custom_config.json --start-date 2025-01-01 --end-date 2026-12-31
```

**Available Modes:**
- **Interactive**: Press SPACE to regenerate, ENTER to save, or Q/ESC to quit
- **Compare**: Tests all schedulers and shows comprehensive performance metrics
- **Analyze**: Detailed schedule analysis with tables, plots, and deadline status

**Available Schedulers:**
- **greedy**: Fast, deterministic scheduling (default)
- **stochastic**: Randomized greedy with multiple attempts
- **lookahead**: Considers future impact of current decisions
- **backtracking**: Can undo decisions when stuck

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
    "enable_blackout_periods": true,
    "conference_response_time_days": 90
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

### Advanced Test Scenarios
- **Blackout Period Boundary Conditions**: Weekend and holiday handling
- **Priority Weight Edge Cases**: Weight application and sorting
- **Backtracking Convergence**: Algorithm stability and solution quality
- **Conference Reassignment Scenarios**: Dynamic conference switching
- **Full 37-Submission Problem**: Complete system validation
- **Performance Benchmarks**: Runtime, memory usage, and quality metrics

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

### Medical Device Development (Primary Use Case)
- **FDA Regulatory Compliance**: Coordinate 17 PCCP modifications with strict timelines
- **Academic Publishing**: Schedule 20+ papers across 14 major conferences
- **Dependency Management**: Handle complex mod-to-paper and paper-to-paper relationships
- **Resource Optimization**: Maintain 1-2 papers in drafting pipeline

### Academic Research Planning
- Schedule multiple paper submissions across conferences
- Manage complex dependency relationships
- Optimize for early completion and quality

### Conference Strategy
- Plan submissions across multiple venues (MICCAI, CVPR, ICML, ARS, etc.)
- Handle biennial vs annual conferences (ICCV runs every 2 years)
- Optimize for acceptance probability and venue compatibility

### Resource Management
- Balance concurrent project capacity (max 2 simultaneous submissions)
- Respect work-life boundaries (weekends, holidays)
- Optimize team utilization and avoid bottlenecks

## 🔬 Advanced Features

### Soft Block Model for PCCP Modifications
Each modification has a flexible completion window with penalties for deviation:
```
BlockStart_m ≤ Finish_m ≤ BlockEnd_m + ε + p_m
```
where ε = 1 month free slack and p_m ≥ 0 incurs penalty cost c_m.

### Concurrency Control
Maintains exactly 1-2 papers in drafting pipeline at all times:
```
1 ≤ Σ_j 1[W_j ≤ t < S_j] ≤ 2  ∀t
```

### Algorithm Implementation Details

#### Stochastic Exploration
- **Priority Randomization**: Base priority × random(0.8, 1.2) noise factor
- **Iteration Tracking**: Multiple attempts with best solution retention
- **Pattern Biasing**: Learning from successful scheduling patterns

#### Lookahead Heuristic
- **30-Day Horizon**: Future impact evaluation window
- **Scoring Factors**: Resource availability, dependent readiness, deadline proximity
- **Weight Balancing**: 0.5 factor for immediate vs future scores

#### Backtracking Capability
- **Decision History**: Maintains undo stack for recent decisions
- **Trigger Conditions**: Utilization drops below 70%
- **Depth Limiting**: Prevents thrashing with maximum backtrack depth

#### Critical Path Analysis
- **Slack Calculation**: Total slack for each submission
- **Zero-Slack Items**: Critical path identification
- **Dynamic Updates**: Real-time slack recalculation during scheduling

### Optimization Objective
The system minimizes a multi-objective function:
```
Minimize: f(x) = w₁ × EarlyCompletion + w₂ × PenaltyCosts - w₃ × ResourceUtilization
```
where:
- EarlyCompletion = Σᵢ priority[i] × start[i]
- PenaltyCosts = Σᵢ∈mods penalty_cost[i] × max(0, start[i] - ready_date[i])
- ResourceUtilization = Σₜ min(active[t], max_concurrent) × (T-t)/T

### Conference Compatibility Matrix
| Paper Type | Venue Type | Penalty $ | Rationale |
|------------|------------|-----------|-----------|
| Engineering-heavy | Clinical/ENT abstract-only | 3000 | Loss of technical audience |
| Clinical | Engineering (ICML/CVPR) | 1500 | Audience mis-match |
| Full-paper capable | Abstract-only venue | 2000 | Reduces publication depth |
| Good match | Good match | 0 | — |

### Slack Cost Formulation
The system calculates penalties for delays and missed opportunities:
```
SlackCost_j = P_j(S_j - S_j,earliest) + Y_j(1_year-deferred) + A_j(1_abstract-miss)
```

| Coefficient | Default $ | Notes |
|-------------|-----------|-------|
| P_j | 1,000 per month (3,000 for J19-J20) | Monthly slip penalty |
| Y_j | 5,000 (10,000 for J19-J20) | Full-year deferral penalty |
| A_j | 3,000 | Missed abstract-only window penalty |

### Paper-to-Paper Dependencies
- **Default lead time**: 3 months between parent and child papers
- **Special cases**: J11→J12 (1 month), J12→J13 (1 month), J19→J20 (2 months)
- **Lead time calculation**: Child paper waits specified months after parent completion

### Mod-to-Mod Dependencies
- **Sequential order**: All mods follow numeric order (1→2→3...→17)
- **Technical dependencies**: 
  - Mod 3 → Mod 4 (Bayesian evidence logic requires SLAM poses)
  - Mod 4 → Mod 5 (Coverage guidance consumes Bayesian confidences)
- **Independent otherwise**: All other mods assumed sequential but independent

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

### Rolling Optimization Cadence
- Re-solve ILP quarterly or on trigger events
- Triggers: Mod slips >2 months, paper misses deadline, resource changes
- FDA submission timing: 0-month gap between mod finish and paper drafting

### Future Development Work
- **ILP Optimizer Integration**: Implement true integer linear programming (e.g., using `pulp`)
- **Advanced Optimizer Module**: Develop `src/optimizer.py` for formal constraint solving
- **Comprehensive Testing**: Add `tests/test_optimizer.py` for optimizer validation
- **Gantt Chart Generation**: Implement automated visualization (matplotlib/plotly)
- **End-to-End Validation**: Verify SlackCost, conference-penalty, and FDA-penalty calculations
- **Real Data Population**: Finalize all mod→paper dependencies and conference mappings

### Implementation Status

#### ✅ Completed Features
- **Blackout Period Support**: Weekend and holiday handling with configurable blackout dates
- **Priority Weighting System**: Engineering papers (2.0), Medical papers (1.0), Mods (1.5), Abstracts (0.5)
- **Penalty Cost Implementation**: Daily penalty calculations with configurable rates
- **Early Abstract Scheduling**: 30-day advance scheduling during slack periods
- **Advanced Algorithms**: Stochastic exploration, 30-day lookahead, backtracking capability
- **Critical Path Analysis**: Slack calculation and zero-slack critical item identification
- **Comprehensive Metrics**: Makespan, utilization, deadline compliance, quality scores

#### 🔄 Medium Priority - Algorithm Enhancements
- **Conference Flexibility**: Dynamic reassignment near deadlines with alternate conference tracking
- **Pause/Resume Support**: Partial progress recording and checkpoint resumption
- **Interactive Mode Improvements**: Real-time metrics display and convergence indicators
- **Local Minima Detection**: Utilization tracking and penalty accumulation monitoring

#### 📋 Lower Priority - Additional Features
- **Conference Response Time**: 90-day response time handling
- **Contingency Recommendations**: Automated fallback conference suggestions
- **Historical Pattern Learning**: Algorithm improvement based on past performance
- **Enhanced Stochastic Exploration**: Iteration tracking and successful pattern biasing

## 📊 Problem Specification

### Paper Portfolio (20 Papers)
The system manages 20 specific papers (J1-J20) with complex dependencies:

| Paper | Title | Draft Window | Conference Families | Dependencies |
|-------|-------|--------------|-------------------|--------------|
| J1 | Computer Vision (CV) endoscopy review | 2 months | ICML, MIDL, CVPR, NeurIPS | Mod 1 |
| J2 | Middle Turbinate/Inferior Turbinate (MT/IT) | 3 months | MICCAI, ARS, IFAR | Mod 2 |
| J3 | Nasal Septal Deviation (NSD) | 3 months | MICCAI, ARS, IFAR | Mod 3, J2 |
| J4 | Eustachian Tube (ET) | 3 months | MICCAI, ARS, IFAR | Mod 4, J3 |
| J5 | Middle Turbinate (MT ???/???) | 2 months | MICCAI, ARS, IFAR | Mod 5 |
| J6 | Eustachian Tube (ET inflamed vs ETDQ) | 2 months | MICCAI, ARS, IFAR | Mod 6, J5 |
| J7 | Mucus | 2 months | ARS, IFAR, AMIA | Mod 7 |
| J8 | Mucus Biology | 2 months | ARS, IFAR, AMIA | Mod 8, J7 |
| J9 | Color | 1 month | CVPR, MIDL, NeurIPS | J8 |
| J10 | Localization (NC Mapping) | 3 months | MICCAI, CVPR | J9 |
| J11 | Polyps | 3 months | MICCAI, ARS, IFAR | Mod 11 |
| J12 | Nasal Polyps (NP) vs PCMT | 2 months | MICCAI, ARS, IFAR | J11 |
| J13 | Polyp color | 1 month | MICCAI, ARS, IFAR | J12 |
| J14 | ???? detection (vs MD) | 3 months | AMIA, MICCAI | Mod 14 |
| J15 | NE AI CDS vs ENT panel | 3 months | AMIA, ARS, IFAR | J14 |
| J16 | NE AI CDS vs PCP panel | 3 months | AMIA, ARS, IFAR | J15 |
| J17 | Gaze tracking vs AI | 2 months | CVPR, AMIA | J16 |
| J18 | Mucus AI vs culture | 2 months | IFAR, ARS | Mod 18 |
| J19 | CT max vs NE Maxillary Mucosa (MM) | 3 months | RSNA, SPIE | Mod 19 |
| J20 | CT eth vs NE Middle Turbinate (MT) | 3 months | RSNA, SPIE | Mod 20, J19 |

### Capacity Analysis
- **Theoretical maximum**: 32 papers across 48 months
- **Planned capacity**: 20 papers (Ed) + ≤5 additional = ≤25 papers
- **Utilization**: ~78% of capacity, leaving room for new ideas
- **Clinical papers**: Can be moved earlier if pipeline gaps exist (e.g., J1, J9, J17)

### Annual Schedule Summary (Historical Reference)
| Year | TotalPaperMonths | PapersCompleted | PeakConcurrency | AvgConcurrency | ModMonths |
|------|------------------|-----------------|-----------------|----------------|-----------|
| 2025 | 5                | 2               | 2               | 0.71           | 2         |
| 2026 | 7                | 2               | 2               | 0.58           | 4         |
| 2027 | 11               | 4               | 2               | 0.92           | 6         |
| 2028 | 16               | 8               | 2               | 1.33           | 5         |
| 2029 | 8                | 4               | 2               | 1.33           | 1         |

### Conference Portfolio (14 Venues)
Major conferences with strict deadlines:

| Conference | Type | Full Papers | Abstract Required | Timing |
|------------|------|-------------|-------------------|--------|
| ICML | Machine Learning | Yes | Yes | July |
| MIDL | Medical Imaging with DL | Yes | Yes | July |
| MICCAI | Medical Imaging & AI | Yes | Yes | October |
| CVPR | Computer Vision | Yes | Yes | June |
| ICCV | Computer Vision (biennial) | Yes | Yes | October (odd years) |
| ARS | American Rhinologic Society | No (abstract-only) | Yes | Fall/Spring |
| RSNA | Radiology | No (abstract-only) | Yes | November/December |
| AMIA | Medical Informatics | Yes | No | November |
| IFAR | International Forum of Allergy | Optional | Yes | March |
| SPIE Medical Imaging | Medical Imaging | Yes | Yes | February |
| EMBC | Biomedical Engineering | Yes | No | July |
| NeurIPS | AI/ML | Yes | Yes | December |

**Note**: ICCV runs biennially (odd-numbered years only). All other conferences repeat annually.

## 📚 API Reference

### Date Utilities (`core.dates`)

The system provides centralized date parsing and utility functions:

```python
from core.dates import parse_date, parse_date_safe, is_working_day, add_working_days

# Parse dates safely
date_obj = parse_date_safe("2025-01-15")  # Returns date object
date_obj = parse_date_safe("invalid", default=date(2025, 1, 1))  # Returns default on error

# Check working days
is_workday = is_working_day(date(2025, 1, 15), blackout_dates)

# Add working days (skipping weekends/holidays)
end_date = add_working_days(start_date, 60, blackout_dates)
```

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