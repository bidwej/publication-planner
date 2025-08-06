"""Constants used throughout the application."""

# Time constants
DAYS_PER_MONTH = 30

# Default time periods
DEFAULT_ABSTRACT_ADVANCE_DAYS = 30
DEFAULT_LOOKAHEAD_DAYS = 30
HEURISTIC_LOOKAHEAD_DAYS = 30
DEFAULT_POSTER_DURATION_DAYS = 30
DEFAULT_PLOT_EXTENSION_DAYS = 90

# True constants (not configurable) - these never change regardless of project

# Scoring constants
MAX_SCORE = 100.0
MIN_SCORE = 0.0
PERCENTAGE_MULTIPLIER = 100.0

# Business logic constants (not configurable - these are algorithm parameters)
TECHNICAL_AUDIENCE_LOSS_PENALTY = 3000.0  # Fixed business rule
AUDIENCE_MISMATCH_PENALTY = 1500.0  # Fixed business rule
DEFAULT_DEPENDENCY_VIOLATION_PENALTY = 50.0  # Fixed business rule

# Efficiency constants (algorithm parameters - not configurable)
OPTIMAL_UTILIZATION_RATE = 0.8  # 80%
UTILIZATION_DEVIATION_PENALTY = 100.0
TIMELINE_EFFICIENCY_SHORT_PENALTY = 0.5
TIMELINE_EFFICIENCY_LONG_PENALTY = 0.8
IDEAL_DAYS_PER_SUBMISSION = 30

# Quality constants (algorithm parameters - not configurable)
ROBUSTNESS_SCALE_FACTOR = 10.0
BALANCE_VARIANCE_FACTOR = 10.0
SINGLE_SUBMISSION_ROBUSTNESS = 100.0
SINGLE_SUBMISSION_BALANCE = 100.0
QUALITY_RESOURCE_FALLBACK_SCORE = 50.0

# Scoring weights (business logic constants - not configurable)
SCORING_QUALITY_DEADLINE_WEIGHT = 0.4
SCORING_QUALITY_DEPENDENCY_WEIGHT = 0.3
SCORING_QUALITY_RESOURCE_WEIGHT = 0.3
SCORING_EFFICIENCY_RESOURCE_WEIGHT = 0.6
SCORING_EFFICIENCY_TIMELINE_WEIGHT = 0.4

# Report penalty factors (business logic constants - not configurable)
REPORT_DEADLINE_VIOLATION_PENALTY = 0.1
REPORT_DEPENDENCY_VIOLATION_PENALTY = 0.15
REPORT_RESOURCE_VIOLATION_PENALTY = 0.2

# Scheduler parameters (algorithm constants - not configurable)
SCHEDULER_RANDOMNESS_FACTOR = 0.1
SCHEDULER_LOOKAHEAD_BONUS_INCREMENT = 0.5

# Validation constants (algorithm parameters - not configurable)
PERFECT_COMPLIANCE_RATE = 100.0  # 100% compliance

# Display constants (UI constants - not configurable)
MAX_TITLE_LENGTH = 30
DEFAULT_DPI = 300

# Report constants (algorithm parameters - not configurable)
MAX_PENALTY_FACTOR = 0.5
PENALTY_NORMALIZATION_FACTOR = 10000.0
REPORT_MAX_SCORE = 1.0
REPORT_MIN_SCORE = 0.0

# Scheduler constants (algorithm parameters - not configurable)
MAX_BACKTRACK_DAYS = 30

# Analytics constants (algorithm parameters - not configurable)
ANALYTICS_DEFAULT_COMPLETION_RATE = 0.0
ANALYTICS_MONTHLY_CONVERSION_FACTOR = 30  # Convert daily to monthly
