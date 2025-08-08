"""Validation module for paper planning constraints."""

# Import main validation functions
from .schedule import (
    validate_all_constraints,
    validate_all_constraints_comprehensive,
    validate_schedule_comprehensive,
    validate_submission_placement,
    validate_submission_comprehensive
)

# Import specific validation functions
from .deadline import (
    validate_deadline_compliance,
    validate_deadline_compliance_single,
    validate_deadline_with_lookahead,
    validate_blackout_dates,
    validate_paper_lead_time_months
)

from .constraints import (
    validate_dependency_satisfaction,
    validate_dependencies_satisfied,
    validate_abstract_paper_dependencies
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
    "validate_all_constraints",
    "validate_all_constraints_comprehensive", 
    "validate_schedule_comprehensive",
    "validate_submission_placement",
    "validate_submission_comprehensive",
    
    # Deadline validation
    "validate_deadline_compliance",
    "validate_deadline_compliance_single",
    "validate_deadline_with_lookahead",
    "validate_blackout_dates",
    "validate_paper_lead_time_months",
    
    # Constraint validation
    "validate_dependency_satisfaction",
    "validate_dependencies_satisfied",
    "validate_abstract_paper_dependencies",
    
    # Resource validation
    "validate_resource_constraints",
    
    # Venue validation
    "validate_conference_compatibility",
    "validate_conference_submission_compatibility",
    "validate_single_conference_policy",
    "validate_venue_compatibility"
]
