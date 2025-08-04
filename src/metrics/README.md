# Metrics Module Structure

## Overview
The metrics module analyzes schedules to provide insights about quality, performance, and compliance.

## Organization

### 1. **Constraints** (`constraints.py`)
Validates that schedules meet business rules and requirements.

- `validate_deadline_compliance()` - Validates deadline adherence
- `validate_dependency_satisfaction()` - Validates dependency relationships  
- `validate_resource_constraints()` - Validates concurrency limits

### 2. **Scoring** (`scoring/`)
Calculates numerical scores and costs for schedule evaluation.

- `scoring/penalty.py` - Calculates penalty scores for violations
- `scoring/quality.py` - Calculates overall quality scores and robustness
- `scoring/efficiency.py` - Calculates efficiency metrics and resource utilization

### 3. **Analytics** (`src/output/analytics.py`)
Provides detailed insights and breakdowns for reporting.

- `analyze_schedule_completeness()` - Schedule completeness analysis
- `analyze_schedule_distribution()` - Time distribution analysis
- `analyze_submission_types()` - Submission type breakdown
- `analyze_timeline()` - Timeline characteristics
- `analyze_resources()` - Resource utilization patterns

### 4. **Reports** (`src/output/`)
Generates formatted reports and summaries.

- `schedule_reporter.py` - Comprehensive schedule reports
- `tables.py` - Tabular output generation
- `console.py` - Console output formatting

## Usage Pattern

```python
# Validation and scoring
from metrics.constraints import validate_deadline_compliance
from metrics.scoring import calculate_penalty_score, calculate_quality_score, calculate_efficiency_score

# Analytics and reporting
from output.analytics import analyze_schedule_completeness, analyze_timeline
from output.schedule_reporter import generate_schedule_report

# Validate constraints
deadline_check = validate_deadline_compliance(schedule, config)

# Calculate scores
penalty_score = calculate_penalty_score(schedule, config)
quality_score = calculate_quality_score(schedule, config)
efficiency_score = calculate_efficiency_score(schedule, config)

# Get analytics
completeness = analyze_schedule_completeness(schedule, config)
timeline = analyze_timeline(schedule, config)

# Generate comprehensive report
report = generate_schedule_report(schedule, config)
```

## Key Principles

1. **Clear separation**: Constraints vs Scoring vs Analytics vs Reports
2. **Consistent naming**: All scoring functions end with `_score`
3. **Public API**: Only main functions are exposed, helpers use `_` prefix
4. **Proper data models**: Using dataclasses for structured return types
5. **Consistent interfaces**: All functions take `(schedule, config)` and return structured data
6. **No circular dependencies**: Each layer is independent
7. **Intuitive naming**: Function names clearly indicate their purpose
8. **Analytics in output**: Reporting and analytics belong in `src/output/` 