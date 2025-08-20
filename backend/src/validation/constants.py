"""Constants validation functions to ensure all constants are within reasonable ranges."""

from typing import List, Dict, Any
from core.constants import (
    SCHEDULING_CONSTANTS, PENALTY_CONSTANTS, EFFICIENCY_CONSTANTS, 
    QUALITY_CONSTANTS, SCORING_CONSTANTS, REPORT_CONSTANTS, 
    DISPLAY_CONSTANTS, ANALYTICS_CONSTANTS
)


def _validate_scheduling_constants() -> List[str]:
    """Validate scheduling constants are within reasonable ranges."""
    errors = []
    
    # Time-related constants
    if SCHEDULING_CONSTANTS.abstract_advance_days < 0:
        errors.append("abstract_advance_days cannot be negative")
    if SCHEDULING_CONSTANTS.lookahead_window_days < 0:
        errors.append("lookahead_window_days cannot be negative")
    if SCHEDULING_CONSTANTS.heuristic_lookahead_days < 0:
        errors.append("heuristic_lookahead_days cannot be negative")
    if SCHEDULING_CONSTANTS.poster_duration_days < 1:
        errors.append("poster_duration_days must be at least 1")
    if SCHEDULING_CONSTANTS.backtrack_limit_days < 0:
        errors.append("backtrack_limit_days cannot be negative")
    
    # Days per month should be reasonable
    if not (28 <= SCHEDULING_CONSTANTS.days_per_month <= 31):
        errors.append("days_per_month must be between 28 and 31")
    
    # Response time should be reasonable
    if SCHEDULING_CONSTANTS.conference_response_time_days < 1:
        errors.append("conference_response_time_days must be at least 1")
    if SCHEDULING_CONSTANTS.conference_response_time_days > 365:
        errors.append("conference_response_time_days should not exceed 1 year")
    
    # Lead time constants
    if SCHEDULING_CONSTANTS.default_paper_lead_time_months < 1:
        errors.append("default_paper_lead_time_months must be at least 1")
    if SCHEDULING_CONSTANTS.work_item_duration_days < 1:
        errors.append("work_item_duration_days must be at least 1")
    if SCHEDULING_CONSTANTS.min_paper_lead_time_days < 1:
        errors.append("min_paper_lead_time_days must be at least 1")
    if SCHEDULING_CONSTANTS.min_abstract_lead_time_days < 1:
        errors.append("min_abstract_lead_time_days must be at least 1")
    
    # Concurrency limits
    if SCHEDULING_CONSTANTS.max_concurrent_submissions < 1:
        errors.append("max_concurrent_submissions must be at least 1")
    if SCHEDULING_CONSTANTS.max_concurrent_submissions > 100:
        errors.append("max_concurrent_submissions should not exceed 100")
    
    return errors


def _validate_penalty_constants() -> List[str]:
    """Validate penalty constants are within reasonable ranges."""
    errors = []
    
    # All penalty values should be non-negative
    if PENALTY_CONSTANTS.technical_audience_loss_penalty < 0:
        errors.append("technical_audience_loss_penalty cannot be negative")
    if PENALTY_CONSTANTS.audience_mismatch_penalty < 0:
        errors.append("audience_mismatch_penalty cannot be negative")
    if PENALTY_CONSTANTS.default_dependency_violation_penalty < 0:
        errors.append("default_dependency_violation_penalty cannot be negative")
    if PENALTY_CONSTANTS.default_mod_penalty_per_day < 0:
        errors.append("default_mod_penalty_per_day cannot be negative")
    if PENALTY_CONSTANTS.default_paper_penalty_per_day < 0:
        errors.append("default_paper_penalty_per_day cannot be negative")
    if PENALTY_CONSTANTS.default_monthly_slip_penalty < 0:
        errors.append("default_monthly_slip_penalty cannot be negative")
    if PENALTY_CONSTANTS.default_full_year_deferral_penalty < 0:
        errors.append("default_full_year_deferral_penalty cannot be negative")
    if PENALTY_CONSTANTS.missed_abstract_penalty < 0:
        errors.append("missed_abstract_penalty cannot be negative")
    
    # Reasonable upper bounds for penalties
    max_reasonable_penalty = 100000.0
    if PENALTY_CONSTANTS.default_paper_penalty_per_day > max_reasonable_penalty:
        errors.append(f"default_paper_penalty_per_day should not exceed {max_reasonable_penalty}")
    if PENALTY_CONSTANTS.default_full_year_deferral_penalty > max_reasonable_penalty:
        errors.append(f"default_full_year_deferral_penalty should not exceed {max_reasonable_penalty}")
    
    return errors


def _validate_efficiency_constants() -> List[str]:
    """Validate efficiency constants are within reasonable ranges."""
    errors = []
    
    # Utilization rate should be between 0 and 1
    if not (0 <= EFFICIENCY_CONSTANTS.optimal_utilization_rate <= 1):
        errors.append("optimal_utilization_rate must be between 0 and 1")
    
    # Penalty values should be non-negative
    if EFFICIENCY_CONSTANTS.utilization_deviation_penalty < 0:
        errors.append("utilization_deviation_penalty cannot be negative")
    if EFFICIENCY_CONSTANTS.timeline_efficiency_short_penalty < 0:
        errors.append("timeline_efficiency_short_penalty cannot be negative")
    if EFFICIENCY_CONSTANTS.timeline_efficiency_long_penalty < 0:
        errors.append("timeline_efficiency_long_penalty cannot be negative")
    
    # Time-related constants
    if EFFICIENCY_CONSTANTS.ideal_days_per_submission < 1:
        errors.append("ideal_days_per_submission must be at least 1")
    
    # Factor constants should be between 0 and 1
    if not (0 <= EFFICIENCY_CONSTANTS.randomness_factor <= 1):
        errors.append("randomness_factor must be between 0 and 1")
    if not (0 <= EFFICIENCY_CONSTANTS.lookahead_bonus_increment <= 1):
        errors.append("lookahead_bonus_increment must be between 0 and 1")
    
    # Safety limits
    if EFFICIENCY_CONSTANTS.max_algorithm_iterations < 1:
        errors.append("max_algorithm_iterations must be at least 1")
    if EFFICIENCY_CONSTANTS.max_algorithm_iterations > 100000:
        errors.append("max_algorithm_iterations should not exceed 100000")
    
    if EFFICIENCY_CONSTANTS.milp_timeout_seconds < 1:
        errors.append("milp_timeout_seconds must be at least 1")
    if EFFICIENCY_CONSTANTS.milp_timeout_seconds > 3600:
        errors.append("milp_timeout_seconds should not exceed 1 hour")
    
    return errors


def _validate_quality_constants() -> List[str]:
    """Validate quality constants are within reasonable ranges."""
    errors = []
    
    # Scale factors should be positive
    if QUALITY_CONSTANTS.robustness_scale_factor <= 0:
        errors.append("robustness_scale_factor must be positive")
    if QUALITY_CONSTANTS.balance_variance_factor <= 0:
        errors.append("balance_variance_factor must be positive")
    
    # Single submission scores should be positive
    if QUALITY_CONSTANTS.single_submission_robustness <= 0:
        errors.append("single_submission_robustness must be positive")
    if QUALITY_CONSTANTS.single_submission_balance <= 0:
        errors.append("single_submission_balance must be positive")
    
    # Fallback score should be reasonable
    if QUALITY_CONSTANTS.quality_resource_fallback_score < 0:
        errors.append("quality_resource_fallback_score cannot be negative")
    
    # Compliance rate constants should be exactly 100
    if QUALITY_CONSTANTS.perfect_compliance_rate != 100.0:
        errors.append("perfect_compliance_rate must be exactly 100.0")
    if QUALITY_CONSTANTS.percentage_multiplier != 100.0:
        errors.append("percentage_multiplier must be exactly 100.0")
    
    return errors


def _validate_scoring_constants() -> List[str]:
    """Validate scoring constants are within reasonable ranges."""
    errors = []
    
    # All weights should be between 0 and 1
    if not (0 <= SCORING_CONSTANTS.quality_deadline_weight <= 1):
        errors.append("quality_deadline_weight must be between 0 and 1")
    if not (0 <= SCORING_CONSTANTS.quality_dependency_weight <= 1):
        errors.append("quality_dependency_weight must be between 0 and 1")
    if not (0 <= SCORING_CONSTANTS.quality_resource_weight <= 1):
        errors.append("quality_resource_weight must be between 0 and 1")
    if not (0 <= SCORING_CONSTANTS.efficiency_resource_weight <= 1):
        errors.append("efficiency_resource_weight must be between 0 and 1")
    if not (0 <= SCORING_CONSTANTS.efficiency_timeline_weight <= 1):
        errors.append("efficiency_timeline_weight must be between 0 and 1")
    
    # Weights should sum to 1 for each category
    quality_sum = (SCORING_CONSTANTS.quality_deadline_weight + 
                   SCORING_CONSTANTS.quality_dependency_weight + 
                   SCORING_CONSTANTS.quality_resource_weight)
    if abs(quality_sum - 1.0) > 0.01:  # Allow small floating point errors
        errors.append(f"Quality weights must sum to 1.0, got {quality_sum}")
    
    efficiency_sum = (SCORING_CONSTANTS.efficiency_resource_weight + 
                      SCORING_CONSTANTS.efficiency_timeline_weight)
    if abs(efficiency_sum - 1.0) > 0.01:
        errors.append(f"Efficiency weights must sum to 1.0, got {efficiency_sum}")
    
    return errors


def _validate_report_constants() -> List[str]:
    """Validate report constants are within reasonable ranges."""
    errors = []
    
    # Score ranges
    if REPORT_CONSTANTS.max_score <= REPORT_CONSTANTS.min_score:
        errors.append("max_score must be greater than min_score")
    
    # Penalty factors should be between 0 and 1
    if not (0 <= REPORT_CONSTANTS.deadline_violation_penalty <= 1):
        errors.append("deadline_violation_penalty must be between 0 and 1")
    if not (0 <= REPORT_CONSTANTS.dependency_violation_penalty <= 1):
        errors.append("dependency_violation_penalty must be between 0 and 1")
    if not (0 <= REPORT_CONSTANTS.resource_violation_penalty <= 1):
        errors.append("resource_violation_penalty must be between 0 and 1")
    
    # Max penalty factor should be reasonable
    if not (0 <= REPORT_CONSTANTS.max_penalty_factor <= 1):
        errors.append("max_penalty_factor must be between 0 and 1")
    
    # Normalization factor should be positive
    if REPORT_CONSTANTS.penalty_normalization_factor <= 0:
        errors.append("penalty_normalization_factor must be positive")
    
    return errors


def _validate_display_constants() -> List[str]:
    """Validate display constants are within reasonable ranges."""
    errors = []
    
    # Title length should be reasonable
    if DISPLAY_CONSTANTS.max_title_length < 10:
        errors.append("max_title_length should be at least 10")
    if DISPLAY_CONSTANTS.max_title_length > 200:
        errors.append("max_title_length should not exceed 200")
    
    # DPI should be reasonable
    if DISPLAY_CONSTANTS.default_dpi < 72:
        errors.append("default_dpi should be at least 72")
    if DISPLAY_CONSTANTS.default_dpi > 600:
        errors.append("default_dpi should not exceed 600")
    
    return errors


def _validate_analytics_constants() -> List[str]:
    """Validate analytics constants are within reasonable ranges."""
    errors = []
    
    # Completion rate should be between 0 and 100
    if not (0 <= ANALYTICS_CONSTANTS.default_completion_rate <= 100):
        errors.append("default_completion_rate must be between 0 and 100")
    
    # Conversion factor should be positive
    if ANALYTICS_CONSTANTS.monthly_conversion_factor <= 0:
        errors.append("monthly_conversion_factor must be positive")
    
    return errors


def validate_constants() -> List[str]:
    """Validate all constants in the application."""
    errors = []
    
    errors.extend(_validate_scheduling_constants())
    errors.extend(_validate_penalty_constants())
    errors.extend(_validate_efficiency_constants())
    errors.extend(_validate_quality_constants())
    errors.extend(_validate_scoring_constants())
    errors.extend(_validate_report_constants())
    errors.extend(_validate_display_constants())
    errors.extend(_validate_analytics_constants())
    
    return errors



