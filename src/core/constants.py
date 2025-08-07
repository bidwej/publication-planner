"""Constants used throughout the application."""

from dataclasses import dataclass

# ===== TIME CONSTANTS =====
# Centralized time-related constants with semantic names

@dataclass
class SchedulingConstants:
    """Core scheduling constants that should be configurable."""
    abstract_advance_days: int = 30
    lookahead_window_days: int = 30
    heuristic_lookahead_days: int = 30  # For heuristic algorithms
    poster_duration_days: int = 30
    backtrack_limit_days: int = 30
    days_per_month: int = 30
    conference_response_time_days: int = 90
    default_paper_lead_time_months: int = 3
    work_item_duration_days: int = 14
    min_paper_lead_time_days: int = 90
    max_concurrent_submissions: int = 3

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
    default_monthly_slip_penalty: float = 1000.0
    default_full_year_deferral_penalty: float = 5000.0
    missed_abstract_penalty: float = 3000.0

# ===== SCORING CONSTANTS =====

@dataclass
class EfficiencyConstants:
    """Constants related to efficiency calculations."""
    optimal_utilization_rate: float = 0.8  # 80%
    utilization_deviation_penalty: float = 100.0
    timeline_efficiency_short_penalty: float = 0.5
    timeline_efficiency_long_penalty: float = 0.8
    ideal_days_per_submission: int = 30
    randomness_factor: float = 0.1  # For stochastic algorithms
    lookahead_bonus_increment: float = 0.5  # For lookahead algorithms

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




