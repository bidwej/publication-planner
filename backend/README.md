# Paper Planner Backend

The backend provides the core scheduling engine, validation system, and data management for the Paper Planner system. It implements sophisticated scheduling algorithms with comprehensive constraint validation and business rule enforcement.

## Overview

The backend consists of several key components:

- **Scheduling Engine**: 7 different scheduling algorithms with comprehensive validation
- **Validation System**: Constraint checking and compliance validation
- **Data Models**: Rich data structures for complex scheduling scenarios
- **Scoring System**: Quality, penalty, and efficiency evaluation
- **Export System**: Multiple output formats and reporting capabilities

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment (copy template and configure paths)
cp env.template .env
# Edit .env to set PYTHONPATH and DATABASE_PATH

# Generate schedule with greedy strategy
python generate_schedule.py --strategy greedy

# Run comprehensive backend operations
python run_backend.py --help

# Run tests
pytest tests/ -v
```

## Environment Configuration

The backend requires proper environment configuration for imports and database access:

### Required Environment Variables
- **PYTHONPATH**: Set to `src` for proper module imports
- **DATABASE_PATH**: Path to SQLite database (default: `../schedules.db`)

### Setup Steps
1. Copy `env.template` to `.env`
2. Update `PYTHONPATH` to point to the `src` directory
3. Set `DATABASE_PATH` to your database location

## Core Components

### 1. Scheduling Algorithms

The scheduler architecture provides a clear separation between different scheduling approaches:

#### Base Scheduler (`BaseScheduler`)
- **Abstract base class** with shared utility methods
- **Comprehensive validation** and constraint satisfaction
- **Dependency management** and resource tracking
- **Conference assignment** and compatibility checking

#### Available Schedulers
- **Greedy**: Fast, priority-based scheduling
- **Heuristic**: Multiple strategy-based approaches
- **Optimal**: MILP optimization (mathematical programming)
- **Random**: Baseline comparison with reproducible results
- **Backtracking**: Conflict resolution through backtracking
- **Lookahead**: Future-aware resource optimization
- **Stochastic**: Probabilistic optimization methods

### 2. Validation System

Comprehensive constraint validation with clean separation of concerns:

#### Validation Modules
- **Deadline Validation**: Conference deadline compliance and blackout dates
- **Resource Validation**: Concurrent submission limits and utilization
- **Schedule Validation**: Comprehensive constraint checking
- **Venue Validation**: Conference compatibility and submission type matching
- **Submission Validation**: Individual submission constraints
- **Scheduler Validation**: Scheduling-specific validation
- **Config Validation**: Configuration integrity and consistency
- **Constants Validation**: Business rule validation

#### Architecture Principles
- **Single public function per module** followed by helper functions
- **Structured results** with consistent `ValidationResult` objects
- **No circular dependencies** through proper module organization
- **Lean core models** with validation logic separated

### 3. Scoring System

Centralized penalty calculation and evaluation:

#### Quality Score (0-100)
- **Deadline Compliance**: 40% weight
- **Dependency Satisfaction**: 30% weight
- **Resource Constraint Compliance**: 30% weight

#### Efficiency Score (0-100)
- **Resource Utilization**: 60% weight (target 80%)
- **Timeline Efficiency**: 40% weight

#### Penalty System
- **Centralized architecture** in `src/scoring/penalties.py`
- **Single source of truth** for all penalty calculations
- **Comprehensive penalty types** including SlackCost and conference compatibility

## Data Consistency & Schema

### Data Structure Consistency ✅
- **32 common fields** between backend and test data
- **0 backend-only fields** and **0 test-only fields**
- Data structures are **fully aligned** between environments
- **29 out of 32 fields** are actively used in the codebase
- **Only 2 fields appear unused** and can be safely deprecated

### Data Schema

#### Papers
**Required Fields:**
- `id` - Unique identifier
- `title` - Paper title

**Optional Fields:**
- `draft_window_months` - Draft preparation time
- `lead_time_from_parents` - Lead time from dependencies
- `preferred_conferences` - Suggested conferences
- `submission_workflow` - Submission process type
- `depends_on` - Dependencies list
- `engineering_ready_date` - When engineering work completes
- `free_slack_months` - Buffer time
- `penalty_cost_per_month` - Monthly penalty cost
- `author` - Author identifier

**Deprecated Fields:**
- `is_biennial` - Removed, use `recurrence` enum instead
- `max_submissions_per_author` - Not implemented

#### Conferences
**Required Fields:**
- `name` - Conference name

**Optional Fields:**
- `conference_type` - MEDICAL or ENGINEERING
- `recurrence` - annual, biennial, quarterly
- `abstract_deadline` - Abstract submission deadline
- `full_paper_deadline` - Paper submission deadline
- `submission_types` - Accepted submission types

#### Configuration
**Required Fields:**
- `min_abstract_lead_time_days` - Minimum abstract lead time
- `min_paper_lead_time_days` - Minimum paper lead time
- `max_concurrent_submissions` - Maximum concurrent submissions
- `data_files` - Data file references

**Optional Fields:**
- `default_paper_lead_time_months` - Default paper lead time
- `work_item_duration_days` - Work item duration
- `conference_response_time_days` - Conference response time
- `max_backtrack_days` - Maximum backtrack days
- `randomness_factor` - Randomness factor
- `lookahead_bonus_increment` - Lookahead bonus
- `penalty_costs` - Penalty cost configuration
- `priority_weights` - Priority weight configuration
- `scheduling_options` - Scheduling options

### Data Consistency Tools

#### Data Consistency Checker
**Location**: `src/validation/data_consistency.py`
**Purpose**: Automated validation of data consistency between environments

**Usage:**
```python
from validation.data_consistency import validate_data_consistency, validate_schema_compliance

# Check consistency between environments
is_consistent, issues = validate_data_consistency(backend_dir, test_dir)

# Check schema compliance
is_compliant, schema_issues = validate_schema_compliance(data_dir)
```

#### Analysis Scripts
- `validate_data_consistency.py` - Basic consistency validation
- `analyze_field_usage.py` - Deep field usage analysis
- `ensure_data_consistency.py` - Complete consistency setup

### Data Quality Recommendations

#### Immediate Actions
- [x] **Deprecate unused fields**: Removed `is_biennial`, use `recurrence` enum instead
- [ ] **Update data files**: Ensure both environments use the same field sets
- [ ] **Run consistency checker**: Use the new checker in CI/CD pipeline

#### Ongoing Maintenance
- [ ] **Regular consistency checks**: Run monthly to catch drift
- [ ] **Schema validation**: Validate new data against schema
- [ ] **Field usage monitoring**: Track which fields are actually used

#### Data Quality Improvements
- [ ] **Fill optional fields**: Improve data completeness
- [ ] **Standardize values**: Ensure consistent data formats
- [ ] **Document field purposes**: Maintain clear field documentation

## Business Rules & Constraints

### 1. Deadline Compliance
- **Primary Constraint**: All submissions must meet conference deadlines
- **Late Penalties**: Configurable per-day penalties (100-3000/day)
- **Lookahead Validation**: Optional buffer time before deadlines

### 2. Dependencies
- **Sequential Dependencies**: Papers depend on completed work items (mods)
- **Dependency Violations**: Heavy penalties for missing dependencies
- **Timing Requirements**: Dependencies must complete before dependent submissions start

### 3. Resource Constraints
- **Concurrent Submissions**: Maximum active submissions at any time
- **Resource Violations**: Penalties for exceeding concurrent limits
- **Utilization Optimization**: Target 80% resource utilization

### 4. Conference Compatibility
- **Type Matching**: Engineering vs Medical conference classification
- **Submission Type Validation**: Abstract, paper, and poster compatibility
- **Single Conference Policy**: One venue per paper per annual cycle

### 5. Advanced Features
- **Working Days Only**: Optional business day restriction
- **Blackout Periods**: Federal holidays and custom unavailable dates
- **Soft Block Model**: PCCP modifications within ±2 months
- **Early Abstract Scheduling**: Configurable advance scheduling

## Configuration Management

### Key Parameters
- `max_concurrent_submissions`: Maximum active submissions (default: 2)
- `min_paper_lead_time_days`: Minimum days for paper preparation (default: 60)
- `min_abstract_lead_time_days`: Minimum days for abstract preparation (default: 30)
- `penalty_costs`: Configurable penalty structure
- `priority_weights`: Submission-specific priority adjustments

### Scheduling Options
- `enable_early_abstract_scheduling`: Allow abstracts to be scheduled early
- `enable_working_days_only`: Restrict scheduling to business days
- `enable_blackout_periods`: Enable blackout date restrictions
- `enable_priority_weighting`: Enable priority-based scheduling

## Backend Runner

The `run_backend.py` script provides comprehensive backend operations:

### Available Operations
1. **Schedule Generation**: Create schedules using different strategies
2. **Analysis**: Analyze existing schedules and generate reports
3. **Validation**: Validate configuration and constraints
4. **Monitoring**: Track schedule progress and detect deviations
5. **Export**: Export schedule data in various formats
6. **Console**: Interactive console interface

### Usage Examples
```bash
# Generate schedule with greedy strategy
python run_backend.py schedule --strategy greedy --config data/config.json

# Validate configuration
python run_backend.py validate --config data/config.json --verbose

# Analyze schedule
python run_backend.py analyze --config data/config.json --schedule schedule.json

# Export to CSV
python run_backend.py export --format csv --output exports/ --config data/config.json
```

## Testing Infrastructure

### Test Organization
```
tests/
├── conftest.py           # Shared test fixtures and configuration
├── core/                 # Core module tests
├── schedulers/           # Scheduler algorithm tests
├── scoring/              # Scoring and penalty tests
├── validation/           # Validation system tests (43 tests)
├── analytics/            # Analytics and reporting tests
└── output/               # Output generation tests
```

### Running Tests
```bash
# Run all tests (fast execution)
pytest -q

# Run specific test categories
pytest tests/validation/ -v      # All validation tests (43 tests)
pytest tests/schedulers/ -v      # Scheduler algorithm tests
pytest tests/core/ -v            # Core module tests
pytest tests/scoring/ -v         # Scoring and penalty tests

# Run with coverage
pytest --cov=src tests/
```

### Test Performance Optimizations
- **MILP Optimization Tests**: 60-second timeout with comprehensive mocking
- **Mock Strategy**: Uses `pytest.monkeypatch` instead of `unittest.mock`
- **Strategic Mocking**: Expensive operations (MILP solver, file I/O) are mocked

## File Structure

```
src/
├── core/           # Core data models and business logic
│   ├── models.py   # Data classes (Submission, Conference, Config)
│   ├── constants.py    # Centralized constants
│   ├── dates.py    # Date utilities and calculations
│   └── config.py   # Configuration loading and parsing
├── validation/     # Constraint validation and compliance checking
│   ├── deadline.py     # Deadline validation and blackout dates
│   ├── schedule.py     # Comprehensive schedule validation
│   ├── submission.py   # Individual submission validation
│   ├── venue.py        # Conference compatibility validation
│   └── resources.py    # Resource constraint validation
├── schedulers/     # Scheduling algorithms
│   ├── base.py     # Base scheduler class
│   ├── greedy.py   # Greedy algorithm
│   ├── backtracking.py  # Backtracking algorithm
│   ├── optimal.py  # MILP optimization
│   ├── stochastic.py  # Stochastic methods
│   ├── lookahead.py  # Lookahead scheduling
│   ├── heuristic.py  # Heuristic algorithms
│   └── random.py   # Random baseline
├── scoring/        # Scoring and evaluation (centralized penalty system)
│   ├── quality.py     # calculate_quality_score()
│   ├── efficiency.py  # calculate_efficiency_score()
│   ├── penalties.py   # calculate_penalty_score() - SINGLE SOURCE OF TRUTH
│   └── aggregator.py  # calculate_schedule_aggregation()
├── output/         # Output generation
│   ├── reports.py  # Report generation
│   ├── analytics.py # Analysis functions
│   ├── console.py  # Console output formatting
│   └── generators/ # Output file generation
└── database/       # Database models and session management
    ├── models.py   # SQLAlchemy models
    └── session.py  # Database session management
```

## Development Guidelines

### Adding New Features
1. Follow the established code structure
2. Add comprehensive tests
3. Update constants in `src/core/constants.py`
4. Document business rules in this README
5. Ensure all constraints are properly validated

### Validation Development
1. **Create validation function in appropriate module**: Add to existing validation module or create new one
2. **Single public function**: Each module should have one main public function followed by helper functions
3. **Return ValidationResult**: Always return structured `ValidationResult` objects
4. **Add comprehensive tests**: Create tests in `tests/validation/` directory
5. **Use existing fixtures**: Leverage `conftest.py` fixtures for test data

### Penalty Calculations
**Always use** `src/scoring/penalties.calculate_penalty_score()` - never calculate penalties directly in other modules.

## Performance

- **Schedule Generation**: < 1 second for 37 submissions
- **Comprehensive Validation**: All constraints validated in < 100ms
- **Memory Usage**: < 100MB for full system
- **Multiple Export Formats**: JSON, CSV, and formatted tables

## Dependencies

### Required Packages
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `pulp`: Mathematical optimization (MILP)
- `plotly`: Chart generation and export
- `sqlalchemy`: Database ORM
- `pydantic`: Data validation and settings management

### Installation
```bash
# Install backend dependencies
pip install -r requirements.txt

# Or install specific packages
pip install pandas numpy pulp plotly sqlalchemy pydantic
```

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure backend environment is properly set up
- Check that all dependencies are installed
- Verify PYTHONPATH configuration

**Configuration Errors**
- Check config file syntax and data file paths
- Validate JSON format and required fields
- Use `python run_backend.py validate` for configuration validation

**Schedule Generation Failures**
- Try different strategies (greedy is most reliable)
- Check constraint configuration
- Verify data file integrity

**Test Failures**
- Run tests with verbose output: `pytest -v`
- Check for missing dependencies
- Verify test data fixtures

### Debug Mode
Use `--verbose` flag for detailed error information:
```bash
python run_backend.py schedule --strategy greedy --config data/config.json --verbose
```

## Future Enhancements

- **Advanced Optimization**: NetworkX integration for dependency analysis
- **Machine Learning**: ML-based optimization recommendations
- **Real-time Updates**: Live schedule monitoring and updates
- **API Endpoints**: RESTful API for external integrations
- **Advanced Analytics**: Predictive modeling and trend analysis
- **Performance Optimization**: Parallel processing and caching
- **Database Integration**: Advanced data persistence and querying
- **Cloud Deployment**: Containerization and cloud infrastructure
