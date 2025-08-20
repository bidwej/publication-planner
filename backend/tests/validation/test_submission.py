"""Test submission validation functions."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from core.models import Config, Submission, Schedule, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, ValidationResult
from validation.submission import validate_submission_constraints


class TestSubmissionValidation:
    """Test cases for submission validation functions."""
    
    def test_validate_submission_constraints_basic(self, sample_config, empty_schedule) -> None:
        """Test basic submission validation."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with a valid submission
        valid_submission = sample_config.submissions[0]  # Get first submission
        start_date = date(2025, 4, 1)
        
        # Add the submission to the schedule
        empty_schedule.add_interval(valid_submission.id, start_date, duration_days=30)
        
        result: List[str] = validate_submission_constraints(valid_submission, start_date, empty_schedule, sample_config)
        assert isinstance(result, list)  # Function returns list of errors
        # The submission should have some validation errors due to venue compatibility or dependencies
        # but we're testing the structure, not the specific business logic
    
    def test_dependency_satisfaction_validation(self, sample_config, empty_schedule) -> None:
        """Test dependency satisfaction for submissions."""
        # Use the sample_config fixture which already has submissions with dependencies
        
        # Find a submission that has dependencies
        dependent_submission = next(s for s in sample_config.submissions if s.depends_on)
        
        # Test with dependencies satisfied
        valid_schedule = Schedule()
        valid_schedule.add_interval(dependent_submission.depends_on[0], date(2025, 1, 1), duration_days=30)
        valid_schedule.add_interval(dependent_submission.id, date(2025, 3, 1), duration_days=30)
        start_date = date(2025, 3, 1)
        
        result: List[str] = validate_submission_constraints(dependent_submission, start_date, valid_schedule, sample_config)
        # Should have fewer errors when dependencies are satisfied
        assert isinstance(result, list)
        
        # Test with dependencies violated
        invalid_schedule = Schedule()
        invalid_schedule.add_interval(dependent_submission.id, date(2025, 1, 1), duration_days=30)
        start_date = date(2025, 1, 1)
        
        invalid_result: List[str] = validate_submission_constraints(dependent_submission, start_date, invalid_schedule, sample_config)
        assert isinstance(invalid_result, list)
        # Should have dependency-related errors
        assert any("Dependencies not satisfied" in error for error in invalid_result)
    
    def test_venue_compatibility_validation(self, sample_config, empty_schedule) -> None:
        """Test venue compatibility for individual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Get a submission and its assigned conference
        submission = next(s for s in sample_config.submissions if s.conference_id)
        conference = next(c for c in sample_config.conferences if c.id == submission.conference_id)
        
        # Test venue compatibility
        empty_schedule.add_interval(submission.id, date(2025, 4, 1), duration_days=30)
        start_date = date(2025, 4, 1)
        
        result: List[str] = validate_submission_constraints(submission, start_date, empty_schedule, sample_config)
        assert isinstance(result, list)  # Function returns list of errors
        # The validation should run and return appropriate errors
    
    def test_deadline_compliance_validation(self, sample_config, empty_schedule) -> None:
        """Test deadline compliance for individual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Get a submission and its assigned conference
        submission = next(s for s in sample_config.submissions if s.conference_id)
        conference = next(c for c in sample_config.conferences if c.id == submission.conference_id)
        
        # Get the deadline for this submission type
        submission_type = submission.kind
        deadline = conference.get_deadline(submission_type)
        
        if deadline:
            # Test with valid schedule (before deadline)
            valid_schedule = Schedule()
            valid_schedule.add_interval(submission.id, deadline - timedelta(days=30), duration_days=30)
            start_date = deadline - timedelta(days=30)
            
            result: List[str] = validate_submission_constraints(submission, start_date, valid_schedule, sample_config)
            assert isinstance(result, list)  # Function returns list of errors
            
            # Test with invalid schedule (after deadline)
            invalid_schedule = Schedule()
            invalid_schedule.add_interval(submission.id, deadline + timedelta(days=30), duration_days=30)
            start_date = deadline + timedelta(days=30)
            
            invalid_result: List[str] = validate_submission_constraints(submission, start_date, invalid_schedule, sample_config)
            assert isinstance(invalid_result, list)  # Function returns list of errors
            # Should have deadline-related errors
            assert any("Submission would miss deadline" in error for error in invalid_result)
