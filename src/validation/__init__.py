"""Validation module for paper planning constraints."""

# Import main validation functions
from .schedule import (
    validate_schedule_constraints,
    validate_schedule_comprehensive,
    analyze_schedule_comprehensive,
    validate_submission_placement,
    validate_submission_in_schedule
)

# Import specific validation functions
from .deadline import (
    validate_deadline_compliance,
    validate_deadline_compliance_single,
    validate_deadline_with_lookahead,
    validate_blackout_dates,
    validate_paper_lead_time_months
)

from .submission import (
    validate_dependencies_satisfied,
    validate_venue_compatibility,
    validate_submission_placement
)

from .resources import (
    validate_resource_constraints
)

from .venue import (
    validate_conference_compatibility,
    validate_conference_submission_compatibility,
    validate_single_conference_policy,
    validate_venue_compatibility
)

# Export main functions for backward compatibility
__all__ = [
    # Main validation functions
    "validate_schedule_constraints",
    "validate_schedule_comprehensive", 
    "analyze_schedule_comprehensive",
    "validate_submission_placement",
    "validate_submission_in_schedule",
    
    # Deadline validation
    "validate_deadline_compliance",
    "validate_deadline_compliance_single",
    "validate_deadline_with_lookahead",
    "validate_blackout_dates",
    "validate_paper_lead_time_months",
    
    # Submission validation
    "validate_dependencies_satisfied",
    "validate_venue_compatibility",
    "validate_submission_placement",
    
    # Resource validation
    "validate_resource_constraints",
    
    # Venue validation
    "validate_conference_compatibility",
    "validate_conference_submission_compatibility",
    "validate_single_conference_policy",
    "validate_venue_compatibility"
]
