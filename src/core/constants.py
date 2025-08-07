"""Constants used throughout the application."""

from dataclasses import dataclass

# ===== CORE SCHEDULING CONSTANTS =====
# These should be configurable via Config dataclass

@dataclass
class SchedulingConstants:
    """Core scheduling constants that should be configurable."""
    default_abstract_advance_days: int = 30
    default_lookahead_days: int = 30
    heuristic_lookahead_days: int = 30
    default_poster_duration_days: int = 30
    default_paper_lead_time_months: int = 3
    work_item_duration_days: int = 14
    conference_response_time_days: int = 90
    max_backtrack_days: int = 30
    randomness_factor: float = 0.1
    lookahead_bonus_increment: float = 0.5

# ===== PENALTY CONSTANTS =====
# These should be configurable via Config.penalty_costs

@dataclass
class PenaltyConstants:
    """Penalty constants that should be configurable."""
    technical_audience_loss_penalty: float = 500.0
    audience_mismatch_penalty: float = 300.0
    default_dependency_violation_penalty: float = 200.0
    default_mod_penalty_per_day: float = 1000.0
    default_paper_penalty_per_day: float = 2000.0

# ===== SCORING CONSTANTS =====

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
class ScoringConstants:
    """Scoring weight constants."""
    quality_deadline_weight: float = 0.4
    quality_dependency_weight: float = 0.3
    quality_resource_weight: float = 0.3
    efficiency_resource_weight: float = 0.6
    efficiency_timeline_weight: float = 0.4

# ===== REPORTING CONSTANTS =====

@dataclass
class ReportConstants:
    """Constants related to reporting."""
    max_score: float = 100.0
    min_score: float = 0.0
    deadline_violation_penalty: float = 0.1
    dependency_violation_penalty: float = 0.15
    resource_violation_penalty: float = 0.2
    max_penalty_factor: float = 0.5
    penalty_normalization_factor: float = 10000.0

# ===== DISPLAY CONSTANTS =====

@dataclass
class DisplayConstants:
    """Constants related to display and UI."""
    max_title_length: int = 30
    default_dpi: int = 300

# ===== ANALYTICS CONSTANTS =====

@dataclass
class AnalyticsConstants:
    """Constants related to analytics calculations."""
    default_completion_rate: float = 0.0
    monthly_conversion_factor: float = 30.0

# ===== CREATE INSTANCES FOR EASY ACCESS =====

SCHEDULING_CONSTANTS = SchedulingConstants()
PENALTY_CONSTANTS = PenaltyConstants()
EFFICIENCY_CONSTANTS = EfficiencyConstants()
QUALITY_CONSTANTS = QualityConstants()
SCORING_CONSTANTS = ScoringConstants()
REPORT_CONSTANTS = ReportConstants()
DISPLAY_CONSTANTS = DisplayConstants()
ANALYTICS_CONSTANTS = AnalyticsConstants()

# ===== LEGACY ALIASES FOR BACKWARD COMPATIBILITY =====
# These will be deprecated in favor of the dataclass constants

# Scheduling constants
DEFAULT_ABSTRACT_ADVANCE_DAYS = SCHEDULING_CONSTANTS.default_abstract_advance_days
DEFAULT_LOOKAHEAD_DAYS = SCHEDULING_CONSTANTS.default_lookahead_days
HEURISTIC_LOOKAHEAD_DAYS = SCHEDULING_CONSTANTS.heuristic_lookahead_days
DEFAULT_POSTER_DURATION_DAYS = SCHEDULING_CONSTANTS.default_poster_duration_days

# Penalty constants
TECHNICAL_AUDIENCE_LOSS_PENALTY = PENALTY_CONSTANTS.technical_audience_loss_penalty
AUDIENCE_MISMATCH_PENALTY = PENALTY_CONSTANTS.audience_mismatch_penalty
DEFAULT_DEPENDENCY_VIOLATION_PENALTY = PENALTY_CONSTANTS.default_dependency_violation_penalty

# Report constants
REPORT_MAX_SCORE = REPORT_CONSTANTS.max_score
REPORT_MIN_SCORE = REPORT_CONSTANTS.min_score
PENALTY_NORMALIZATION_FACTOR = REPORT_CONSTANTS.penalty_normalization_factor
MAX_PENALTY_FACTOR = REPORT_CONSTANTS.max_penalty_factor
REPORT_DEADLINE_VIOLATION_PENALTY = REPORT_CONSTANTS.deadline_violation_penalty
REPORT_DEPENDENCY_VIOLATION_PENALTY = REPORT_CONSTANTS.dependency_violation_penalty
REPORT_RESOURCE_VIOLATION_PENALTY = REPORT_CONSTANTS.resource_violation_penalty

# Analytics constants
ANALYTICS_DEFAULT_COMPLETION_RATE = ANALYTICS_CONSTANTS.default_completion_rate
ANALYTICS_MONTHLY_CONVERSION_FACTOR = ANALYTICS_CONSTANTS.monthly_conversion_factor
PERCENTAGE_MULTIPLIER = QUALITY_CONSTANTS.percentage_multiplier

# Display constants
MAX_TITLE_LENGTH = DISPLAY_CONSTANTS.max_title_length

# Quality constants
PERFECT_COMPLIANCE_RATE = QUALITY_CONSTANTS.perfect_compliance_rate
MIN_SCORE = REPORT_CONSTANTS.min_score
