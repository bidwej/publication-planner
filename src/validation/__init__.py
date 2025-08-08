"""Validation module for paper planning constraints."""

# Re-export all the main validation functions
from .temporal import (
    validate_deadline_compliance,
    validate_deadline_compliance_single,
    validate_deadline_with_lookahead,
    validate_blackout_dates,
    validate_paper_lead_time_months,
    _validate_early_abstract_scheduling,
    _validate_conference_response_time,
    _validate_working_days_only
)

from .dependencies import (
    validate_dependency_satisfaction,
    validate_dependencies_satisfied,
    validate_abstract_paper_dependencies
)

from .concurrency import (
    validate_resource_constraints,
    _calculate_daily_load
)

from .venue_rules import (
    validate_conference_compatibility,
    validate_conference_submission_compatibility,
    validate_single_conference_policy,
    validate_venue_compatibility
)

from .penalties import (
    validate_priority_weighting
)

from .recurrence import (
    validate_soft_block_model
)

from .comprehensive import (
    validate_all_constraints,
    validate_all_constraints_comprehensive,
    validate_schedule_comprehensive,
    validate_single_submission_constraints,
    validate_single_submission_constraints_comprehensive,
    validate_scheduling_options,
    _calculate_comprehensive_scores,
    _calculate_comprehensive_analytics
)

from .utilities import (
    is_working_day,
    _get_next_deadline
)

# Legacy function names for backward compatibility
from .comprehensive import validate_submission_placement, validate_submission_comprehensive
validate_single_submission_constraints = validate_submission_placement
validate_single_submission_constraints_comprehensive = validate_submission_comprehensive

__all__ = [
    # Temporal validations
    "validate_deadline_compliance",
    "validate_deadline_compliance_single", 
    "validate_deadline_with_lookahead",
    "validate_blackout_dates",
    "validate_paper_lead_time_months",
    "_validate_early_abstract_scheduling",
    "_validate_conference_response_time",
    "_validate_working_days_only",
    
    # Dependency validations
    "validate_dependency_satisfaction",
    "validate_dependencies_satisfied",
    "validate_abstract_paper_dependencies",
    
    # Concurrency validations
    "validate_resource_constraints",
    "_calculate_daily_load",
    
    # Venue rule validations
    "validate_conference_compatibility",
    "validate_conference_submission_compatibility", 
    "validate_single_conference_policy",
    "validate_venue_compatibility",
    
    # Penalty validations
    "validate_priority_weighting",
    
    # Recurrence validations
    "validate_soft_block_model",
    
    # Comprehensive validations
    "validate_all_constraints",
    "validate_all_constraints_comprehensive",
    "validate_schedule_comprehensive",
    "validate_single_submission_constraints",
    "validate_single_submission_constraints_comprehensive",
    "validate_scheduling_options",
    "_calculate_comprehensive_scores",
    "_calculate_comprehensive_analytics",
    
    # Utility functions
    "is_working_day",
    "_get_next_deadline"
]
