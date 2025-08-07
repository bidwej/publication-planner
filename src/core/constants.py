"""Constants used throughout the application."""

from dataclasses import dataclass

# Default time periods
DEFAULT_ABSTRACT_ADVANCE_DAYS = 30
DEFAULT_LOOKAHEAD_DAYS = 30
HEURISTIC_LOOKAHEAD_DAYS = 30
DEFAULT_POSTER_DURATION_DAYS = 30
DEFAULT_PLOT_EXTENSION_DAYS = 90

# Legacy constants for backward compatibility
MIN_SCORE = 0.0
TECHNICAL_AUDIENCE_LOSS_PENALTY = 500.0
AUDIENCE_MISMATCH_PENALTY = 300.0
DEFAULT_DEPENDENCY_VIOLATION_PENALTY = 200.0

# Report constants
REPORT_MAX_SCORE = 100.0
REPORT_MIN_SCORE = 0.0
PENALTY_NORMALIZATION_FACTOR = 10000.0
MAX_PENALTY_FACTOR = 0.5
REPORT_DEADLINE_VIOLATION_PENALTY = 0.1
REPORT_DEPENDENCY_VIOLATION_PENALTY = 0.15
REPORT_RESOURCE_VIOLATION_PENALTY = 0.2

# Analytics constants
ANALYTICS_DEFAULT_COMPLETION_RATE = 0.0
ANALYTICS_MONTHLY_CONVERSION_FACTOR = 30.0
PERCENTAGE_MULTIPLIER = 100.0

# Display constants
MAX_TITLE_LENGTH = 30

# Quality constants
PERFECT_COMPLIANCE_RATE = 100.0

# Structured constants for better organization
@dataclass
class EfficiencyConstants:
    """Constants related to efficiency calculations."""
    optimal_utilization_rate: float = 0.8  # 80%
    utilization_deviation_penalty: float = 100.0
    timeline_efficiency_short_penalty: float = 0.5
    timeline_efficiency_long_penalty: float = 0.8
    ideal_days_per_submission: int = 30


@dataclass
class QualityConstants:
    """Constants related to quality calculations."""
    robustness_scale_factor: float = 10.0
    balance_variance_factor: float = 10.0
    single_submission_robustness: float = 100.0
    single_submission_balance: float = 100.0
    quality_resource_fallback_score: float = 50.0
    perfect_compliance_rate: float = 100.0
    percentage_multiplier: float = 100.0


@dataclass
class ScoringWeights:
    """Scoring weight constants."""
    quality_deadline_weight: float = 0.4
    quality_dependency_weight: float = 0.3
    quality_resource_weight: float = 0.3
    efficiency_resource_weight: float = 0.6
    efficiency_timeline_weight: float = 0.4


@dataclass
class ReportConstants:
    """Constants related to reporting."""
    deadline_violation_penalty: float = 0.1
    dependency_violation_penalty: float = 0.15
    resource_violation_penalty: float = 0.2
    max_penalty_factor: float = 0.5
    penalty_normalization_factor: float = 10000.0


@dataclass
class SchedulerConstants:
    """Constants related to scheduler algorithms."""
    randomness_factor: float = 0.1
    lookahead_bonus_increment: float = 0.5
    max_backtrack_days: int = 30


@dataclass
class DisplayConstants:
    """Constants related to display and UI."""
    max_title_length: int = 30
    default_dpi: int = 300


@dataclass
class AnalyticsConstants:
    """Constants related to analytics calculations."""
    default_completion_rate: float = 0.0
    monthly_conversion_factor: float = 30.0


# Create instances for easy access
EFFICIENCY_CONSTANTS = EfficiencyConstants()
QUALITY_CONSTANTS = QualityConstants()
SCORING_WEIGHTS = ScoringWeights()
REPORT_CONSTANTS = ReportConstants()
SCHEDULER_CONSTANTS = SchedulerConstants()
DISPLAY_CONSTANTS = DisplayConstants()
ANALYTICS_CONSTANTS = AnalyticsConstants()
