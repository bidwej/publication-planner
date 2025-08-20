"""Constants used throughout the application."""

from dataclasses import dataclass

# ===== TIME CONSTANTS =====
# Centralized time-related constants with semantic names

@dataclass
class SchedulingConstants:
    """Constants related to scheduling algorithms and constraints."""
    abstract_advance_days: int = 30
    lookahead_window_days: int = 30
    heuristic_lookahead_days: int = 30  # For heuristic algorithms
    poster_duration_days: int = 30
    backtrack_limit_days: int = 30
    days_per_month: int = 30
    conference_response_time_days: int = 90
    default_paper_lead_time_months: int = 3
    # Additional scheduling constants
    work_item_duration_days: int = 14
    min_paper_lead_time_days: int = 90
    min_abstract_lead_time_days: int = 30
    max_concurrent_submissions: int = 3
    # Threshold constants for penalties
    months_delay_threshold: int = 12
    abstract_missed_threshold: int = 6
    paper_missed_threshold: int = 4
    poster_missed_threshold: int = 3
    # Reference period constants
    reference_period_days: int = 365  # 1 year reference period for validation

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
    # Additional penalty constants for hardcoded values
    resource_violation_penalty: float = 200.0
    soft_block_violation_penalty: float = 200.0
    single_conference_violation_penalty: float = 500.0
    lead_time_violation_penalty: float = 150.0
    conference_compatibility_penalty: float = 300.0
    abstract_paper_dependency_penalty: float = 400.0
    # Multiplier constants for penalty calculations
    deadline_mismatch_multiplier: float = 1.2
    missing_dependency_multiplier: float = 2.0

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
    max_algorithm_iterations: int = 1000  # Safety limit for greedy algorithms
    milp_timeout_seconds: int = 60  # MILP solver timeout in seconds (increased from 10)
    # Utilization threshold for over-utilization detection
    over_utilization_threshold: float = 1.2

@dataclass
class PriorityConstants:
    """Constants related to priority weighting."""
    paper_weight: float = 1.0
    mod_weight: float = 1.5
    abstract_weight: float = 0.5
    # Base priority values for scheduler algorithms
    base_paper_priority: float = 5.0
    base_abstract_priority: float = 3.0
    base_poster_priority: float = 1.0
    dependency_bonus: float = 10.0
    deadline_proximity_factor: float = 100.0

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
    # Compliance bonus and threshold values
    compliance_bonus: float = 0.05
    high_compliance_threshold: float = 95.0
    # Score thresholds for status evaluation
    excellent_score_threshold: float = 80.0
    good_score_threshold: float = 60.0
    fair_score_threshold: float = 40.0

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
PRIORITY_CONSTANTS = PriorityConstants()
QUALITY_CONSTANTS = QualityConstants()
SCORING_CONSTANTS = ScoringConstants()
REPORT_CONSTANTS = ReportConstants()
DISPLAY_CONSTANTS = DisplayConstants()
ANALYTICS_CONSTANTS = AnalyticsConstants()




