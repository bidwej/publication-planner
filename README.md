# Paper Planner

An academic paper scheduling system that optimizes the submission timeline for research papers, abstracts, and posters while respecting various constraints and business rules.

## Overview

The Paper Planner is designed to help researchers and teams efficiently schedule their academic submissions across multiple conferences and journals. It considers deadlines, dependencies, resource constraints, and various business rules to create optimal schedules.

### Interactive Features

**✅ Interactive Gantt Charts (Plotly):**
- Zoom and pan through schedules
- Hover for detailed information
- Color-coded by priority and type
- Export to HTML/PNG/SVG

**✅ Real-time Analytics:**
- Resource utilization tracking
- Deadline compliance analysis
- Strategy comparison

**✅ Web Dashboard:**
- Dropdown strategy selection
- Live chart updates
- Responsive design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Paper-Planner
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

#### Web Charts (Dashboard & Timeline)
```bash
# Dashboard mode (full features)
python run_web_charts.py --mode dashboard

# Timeline mode (timeline only)
python run_web_charts.py --mode timeline

# Capture screenshots
python run_web_charts.py --mode dashboard --capture
```
- **Dashboard URL**: http://127.0.0.1:8050
- **Timeline URL**: http://127.0.0.1:8051
- **Features**: Interactive charts, real-time updates, strategy selection
- **Debug Mode**: Disabled for stability

#### Command Line Interface
```bash
python generate_schedule.py
```
- **Output**: Console-based schedule generation
- **Export**: JSON and CSV files
- **Configuration**: Uses `config.json` in root directory

### Configuration
- **Main Config**: `config.json` in root directory
- **Custom Penalties**: Adjustable via config file
- **Business Rules**: All constraints configurable
- **Output Settings**: Configurable export formats

### Troubleshooting

#### Common Issues

**ModuleNotFoundError: No module named 'dash'**
```bash
pip install -r requirements.txt
```

**Virtual Environment Not Activated**
```bash
# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

**Port Already in Use**
- The dashboard runs on port 8050 by default
- The timeline runs on port 8051 by default
- If port is busy, modify `run_web_charts.py` to use a different port
- Or kill the process using the port: `netstat -ano | findstr :8050`

**PowerShell Execution Policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Development Tips
- **Debug Mode**: Always enabled in development
- **Hot Reload**: Changes to Python files auto-reload the server
- **Error Logging**: Check console output for detailed error messages
- **Browser Console**: Use F12 for client-side debugging

## Core Concepts

### Submission Types
- **Papers**: Full research papers with extended timelines
- **Abstracts**: Conference abstracts with shorter timelines  
- **Posters**: Poster presentations with minimal timelines
- **Mods**: Modified versions of existing papers

### Conference Types
- **Medical/Clinical**: Healthcare-focused conferences (e.g., SAGES, DDW)
- **Engineering**: Technical/engineering conferences (e.g., ICRA, IROS)
- **Hybrid**: Conferences accepting both medical and engineering papers

## Business Rules & Constraints

### 1. Deadline Compliance
- **Primary Constraint**: All submissions must meet their conference/journal deadlines
- **Late Penalties**: Configurable per-day penalties for missed deadlines
- **Configurable Penalties**: All penalty values can be adjusted via config.json
- **Lookahead Validation**: Optional buffer time before deadlines for safety

### 2. Dependencies
- **Sequential Dependencies**: Some submissions depend on others (e.g., paper depends on abstract)
- **Dependency Violations**: Heavy penalties for missing dependencies
- **Timing Requirements**: Dependencies must complete before dependent submissions start
- **Lead Time Requirements**: Configurable lead time between dependency completion and dependent start

### 3. Resource Constraints
- **Concurrent Submissions**: Maximum number of active submissions at any time
- **Resource Violations**: Penalties for exceeding concurrent limits
- **Utilization Optimization**: Prefer 80% resource utilization for efficiency
- **Daily Load Tracking**: Comprehensive tracking of daily workload distribution

### 4. Conference Compatibility Matrix

| Paper Type | Conference Type | Abstract-Only | Full-Paper | Penalty |
|------------|----------------|---------------|------------|---------|
| Engineering | Medical | ✓ | ❌ | 3000 (Technical audience loss) |
| Clinical | Engineering | ❌ | ✓ | 1500 (Audience mismatch) |
| Engineering | Engineering | ✓ | ✓ | 0 (Optimal) |
| Clinical | Medical | ✓ | ✓ | 0 (Optimal) |
| Any | Abstract-Only | ❌ | ❌ | 2000 (Reduced publication depth) |

### 5. Submission Type Rules
- **Papers**: Require 60-90 days lead time depending on complexity
- **Abstracts**: Can be scheduled closer to deadlines (30 days advance)
- **Posters**: Minimal timeline requirements (30 days default)
- **Mods**: Inherit timeline requirements from original submission
- **Draft Window Configuration**: Configurable months for each submission type

### 6. Priority System
- **Engineering Papers**: Weight 2.0 (highest priority)
- **Medical Papers**: Weight 1.0 (standard priority)
- **Mods**: Weight 1.5 (intermediate priority)
- **Abstracts**: Weight 0.5 (lower priority)
- **Configurable Weights**: All priority weights adjustable via config

### 7. Blackout Periods
- **Federal Holidays**: Automatic blackout dates for federal holidays
- **Custom Blackout Periods**: Configurable custom blackout date ranges
- **Working Days Only**: Optional restriction to business days only
- **Blackout Violations**: Penalties for scheduling on blackout dates

### 8. Single Conference Policy
- **One Venue Per Paper**: Each paper can only be submitted to one venue per annual cycle
- **Policy Violations**: Penalties for multiple venue assignments
- **Annual Cycle Tracking**: Automatic detection of policy violations

### 9. Soft Block Model (PCCP)
- **±2 Month Window**: Modifications must be scheduled within ±2 months of earliest start date
- **Deviation Penalties**: Penalties for scheduling outside the soft block window
- **Configurable Tolerance**: Adjustable tolerance for soft block violations

### 10. Conference Response Time
- **Response Buffer**: Configurable buffer time for conference response processing
- **Response Violations**: Penalties for insufficient response time
- **Paper-Specific Rules**: Different response times for different submission types

### 11. Early Abstract Scheduling
- **Advance Scheduling**: Abstracts can be scheduled earlier than deadlines
- **Configurable Advance**: Adjustable advance days for early abstract scheduling
- **Abstract-Only Venues**: Special handling for abstract-only conference venues

### 12. Working Days Only
- **Business Day Scheduling**: Optional restriction to business days only
- **Weekend Exclusion**: Automatic exclusion of weekends (Saturday/Sunday)
- **Blackout Date Integration**: Integration with blackout periods
- **Working Day Calculation**: Proper calculation of working days for durations

### 13. Comprehensive Date Utilities
- **Safe Date Parsing**: Robust date parsing with fallback values
- **Working Day Addition**: Add working days while skipping weekends/blackouts
- **Date Formatting**: Multiple date formatting options (display, compact, relative)
- **Duration Calculations**: Human-readable duration formatting
- **Relative Time**: "In X days", "X weeks ago", etc.

### 14. Conference Submission Type Validation
- **Abstract-Only Conferences**: Some conferences only accept abstracts (e.g., RSNA, IFAR)
- **Paper-Only Conferences**: Some conferences only accept papers (e.g., ICRA, AMIA Annual)
- **Abstract + Paper Conferences**: Some require abstract submission before paper (e.g., ICML, MICCAI)
- **Poster-Only Conferences**: Some conferences only accept posters
- **All-Types Conferences**: Some accept all submission types
- **Abstract-to-Paper Dependencies**: Papers may require corresponding abstract submissions
- **Submission Type Compatibility**: Validates that submissions match conference requirements
- **Conference Submission Types**: 
  - `ABSTRACT_ONLY`: Only accepts abstracts
  - `PAPER_ONLY`: Only accepts papers
  - `POSTER_ONLY`: Only accepts posters
  - `ABSTRACT_AND_PAPER`: Requires abstract before paper
  - `ABSTRACT_OR_PAPER`: Accepts either abstract or paper
  - `ALL_TYPES`: Accepts all submission types
- **Automatic Detection**: Conference submission types are auto-detected from deadline configuration
- **Compatibility Validation**: Ensures submissions match conference requirements

### 15. Abstract-to-Paper Dependencies
- **Required Dependencies**: Papers at conferences requiring abstracts must have corresponding abstract submissions
- **Timing Validation**: Abstracts must be scheduled before their corresponding papers
- **Naming Convention**: Abstract submissions follow pattern `{paper_id}-abs` for automatic linking
- **Missing Abstract Detection**: Identifies papers missing required abstract submissions
- **Timing Violation Detection**: Identifies papers scheduled before their required abstracts
- **Conference-Specific Rules**: Different conferences have different abstract requirements

## Scoring System

### Quality Score (0-100)
- **Deadline Compliance**: 40% weight
- **Dependency Satisfaction**: 30% weight  
- **Resource Constraint Compliance**: 30% weight
- **Robustness**: Buffer time between submissions for disruption resilience
- **Balance**: Even distribution of workload over time

### Efficiency Score (0-100)
- **Resource Utilization**: 60% weight (target 80% utilization)
- **Timeline Efficiency**: 40% weight (optimal duration per submission)
- **Peak Load Optimization**: Minimize maximum concurrent submissions
- **Average Load Optimization**: Optimize average daily workload

### Penalty System
- **Deadline Violations**: Per-day penalties (100-3000/day)
- **Dependency Violations**: 50 points per day of violation
- **Resource Violations**: 200 points per excess submission
- **Conference Compatibility**: 1500-3000 points per mismatch
- **Conference Submission Type Violations**: High penalties for incompatible submission types
- **Abstract-to-Paper Dependency Violations**: High penalties for missing required abstracts
- **Slack Cost Penalties**: 
  - **Monthly Slip Penalty (P_j)**: Penalty per month of delay from earliest start date
  - **Full-Year Deferral Penalty (Y_j)**: Additional penalty if delayed by 12+ months
  - **Missed Abstract Penalty (A_j)**: Penalty for missing abstract-only submission windows
  - **Formula**: `Total Slack Cost = P_j × months_delay + Y_j × (if months_delay ≥ 12) + A_j × missed_abstracts`
- **Blackout Violations**: Penalties for scheduling on blackout dates
- **Soft Block Violations**: Penalties for PCCP model violations
- **Single Conference Violations**: Penalties for multiple venue assignments
- **Response Time Violations**: Penalties for insufficient conference response time
- **Slack Cost Penalties**: Monthly slip penalties and full-year deferral penalties

## Scheduling Algorithms

### 1. Greedy Scheduler
- Prioritizes submissions by deadline and priority
- Simple, fast, but may not find optimal solutions

### 2. Backtracking Scheduler  
- Explores multiple scheduling paths
- Can find optimal solutions but slower
- Uses constraint satisfaction techniques

### 3. Heuristic Scheduler
- Combines multiple heuristics for better solutions
- Balances speed and quality

### 4. Lookahead Scheduler
- Considers future implications of current decisions
- Uses 30-day lookahead window by default

### 5. Random Scheduler
- Generates random valid schedules
- Useful for baseline comparisons

### 6. Stochastic Scheduler
- Uses probabilistic methods for optimization
- Good for complex constraint scenarios

### 7. Optimal Scheduler
- Finds mathematically optimal solutions
- Computationally expensive but highest quality

## Configuration

### Key Parameters
- `max_concurrent_submissions`: Maximum active submissions (default: 2)
- `min_paper_lead_time_days`: Minimum days for paper preparation (default: 60)
- `min_abstract_lead_time_days`: Minimum days for abstract preparation (default: 30)
- `penalty_costs`: Configurable penalty structure
- `priority_weights`: Submission-specific priority adjustments
- `default_paper_lead_time_months`: Default months for paper preparation (default: 3)

### Scheduling Options
- `enable_early_abstract_scheduling`: Allow abstracts to be scheduled early
- `abstract_advance_days`: How early abstracts can be scheduled (default: 30)
- `enable_working_days_only`: Restrict scheduling to business days
- `enable_blackout_periods`: Enable blackout date restrictions
- `conference_response_time_days`: Buffer time for conference responses (default: 90)
- `enable_priority_weighting`: Enable priority-based scheduling
- `enable_dependency_tracking`: Enable dependency validation
- `enable_concurrency_control`: Enable resource constraint validation

### Data Files
- `conferences.json`: Conference definitions and deadlines
- `mods.json`: Modification/abstract submissions
- `papers.json`: Full paper submissions
- `blackouts.json`: Blackout dates (federal holidays, custom periods)

## Output Formats

### 1. Interactive Gantt Charts (Plotly)
- **Zoom and Pan**: Navigate through complex schedules
- **Hover Details**: See submission details, deadlines, conferences
- **Color Coding**: By priority, type, and status
- **Export Options**: HTML, PNG, SVG formats
- **Web-Ready**: Share via HTML files

### 2. Static Visualizations (Matplotlib)
- **Fast Generation**: Quick chart creation
- **Report-Ready**: Perfect for documentation
- **Lightweight**: No web dependencies

### 3. Web Dashboard (Dash)
- **Interactive Interface**: Dropdown strategy selection
- **Real-Time Updates**: Live chart updates
- **Responsive Design**: Mobile-friendly
- **Strategy Comparison**: Side-by-side analysis

### 4. Schedule Summary
- Timeline visualization (Gantt charts)
- Resource utilization plots
- Deadline compliance analysis
- **Monthly Tables**: Monthly breakdown of active submissions
- **Deadline Tables**: Detailed deadline compliance tracking
- **Metrics Tables**: Comprehensive performance metrics

### 5. Quality Metrics
- Overall schedule score (0-100)
- Constraint violation counts
- Penalty breakdown by category
- **Robustness Analysis**: Buffer time and disruption resilience
- **Balance Metrics**: Workload distribution analysis
- **Comprehensive Validation**: All constraint types validated

### 6. Efficiency Analysis
- Resource utilization rates
- Timeline efficiency scores
- Workload distribution analysis
- **Peak Load Optimization**: Minimize maximum concurrent submissions
- **Average Load Optimization**: Optimize average daily workload
- **Timeline Span Analysis**: Optimal schedule duration

### 7. Reports
- **JSON-formatted detailed reports**: Complete schedule data in JSON format
- **CSV exports for external analysis**: Table data in CSV format
- **Console-friendly summaries**: Formatted output for terminal display
- **Comprehensive Report Generation**: All metrics, constraints, and analytics
- **Timestamped Output Directories**: Organized output with timestamps
- **Multiple Export Formats**: JSON, CSV, and formatted tables

## Usage Examples

### Command Line Usage
```bash
# Generate schedule with greedy strategy
python generate_schedule.py greedy

# Interactive mode
python generate_schedule.py
```

### Web Interface (Interactive)
```bash
# Start the web dashboard
python run_web_charts.py --mode dashboard

# Start the timeline view
python run_web_charts.py --mode timeline

# Open browser to: http://127.0.0.1:8050 (dashboard) or http://127.0.0.1:8051 (timeline)
```

### Basic Usage
```python
from planner import Planner

# Load configuration
planner = Planner("config.json")

# Generate schedule
result = planner.schedule()

# Get metrics
metrics = planner.get_schedule_metrics()
print("Overall Score: %s", metrics.overall_score)
```

### Interactive Visualization
```python
from app.components.charts.gantt_chart import create_gantt_chart

fig = create_gantt_chart(schedule, submissions, config)
fig.show()  # Opens in browser
fig.write_html("schedule.html")  # Save for sharing
```

### Advanced Configuration
```python
# Custom penalty structure
config = {
    "penalty_costs": {
        "default_penalty_per_day": 100.0,
        "resource_violation_penalty": 200.0,
        "dependency_violation_penalty": 50.0
    },
    "scheduling_options": {
        "enable_early_abstract_scheduling": True,
        "abstract_advance_days": 45
    }
}
```

## File Structure

```
src/
├── core/           # Core data models and business logic
│   ├── models.py   # Data classes (Submission, Conference, Config)
│   ├── constraints.py  # Constraint validation logic
│   ├── constants.py    # Centralized constants
│   └── config.py   # Configuration loading and parsing
├── schedulers/     # Scheduling algorithms
│   ├── base.py     # Base scheduler class
│   ├── greedy.py   # Greedy algorithm
│   ├── backtracking.py  # Backtracking algorithm
│   ├── optimal.py  # MILP optimization
│   ├── stochastic.py  # Stochastic methods
│   ├── lookahead.py  # Lookahead scheduling
│   ├── heuristic.py  # Heuristic algorithms
│   └── random.py   # Random baseline
├── scoring/        # Scoring and evaluation
│   ├── quality.py  # Quality metrics
│   ├── efficiency.py  # Efficiency metrics
│   └── penalty.py  # Penalty calculations
├── output/         # Output generation
│   ├── reports.py  # Report generation
│   ├── analytics.py # Analysis functions
│   ├── console.py  # Console output formatting
│   ├── tables.py   # Table generation
│   ├── generators/ # Output file generation
│   └── formatters/ # Data formatting utilities
└── planner.py      # Main planner interface

app/
├── main.py         # Dash web application
├── models.py       # Web app data models
├── storage.py      # Data persistence
├── components/     # UI components
│   ├── charts/     # Interactive charts
│   │   ├── gantt_chart.py      # Gantt chart component
│   │   ├── gantt_formatter.py  # Chart formatting
│   │   └── metrics_chart.py    # Metrics visualization
│   └── tables/     # Data tables
│       └── schedule_table.py   # Schedule display table
└── layouts/        # Page layouts
    ├── header.py   # Application header
    ├── sidebar.py  # Navigation sidebar
    └── main_content.py # Main content area
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/schedulers/ -v
pytest tests/core/ -v
pytest tests/output/ -v
```

All tests should pass to ensure system integrity.

## Contributing

When adding new features:
1. Follow the established code structure
2. Add comprehensive tests
3. Update constants in `src/core/constants.py`
4. Document business rules in this README
5. Ensure all constraints are properly validated

## Performance

- **Schedule Generation**: < 1 second for 37 submissions
- **Interactive Charts**: Real-time updates
- **Web Dashboard**: Responsive, mobile-friendly
- **Memory Usage**: < 100MB for full system
- **Comprehensive Validation**: All constraints validated in < 100ms
- **Multiple Export Formats**: JSON, CSV, and formatted tables
- **Timestamped Output**: Organized output directories with timestamps

## Development Tools

### Archive Scripts
- **Source Code Archiving**: `scripts/archive_source.py` - Create clean source archives
- **Package Copying**: `scripts/copy_package.py` - Copy packages with exclusions
- **Source Concatenation**: `scripts/concat_source.py` - Combine source files

### Testing Framework
- **Comprehensive Test Suite**: 100+ tests covering all components
- **Test Categories**: Core, schedulers, scoring, output, metrics
- **Test Data**: Common test data and fixtures
- **Validation Testing**: All constraint and scoring functions tested

## License

This project is licensed under the MIT License - see the LICENSE file for details.