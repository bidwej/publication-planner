from typing import Dict, List, Any, Optional

"""
Tests for submission validation module.
"""

import pytest
from datetime import date, timedelta
from src.validation.submission import validate_submission_constraints
from core.models import Config, Submission


class TestSubmissionValidation:
    """Test cases for submission validation functions."""
    
    def test_validate_submission_constraints_basic(self, sample_config) -> None:
        """Test basic submission validation."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with a valid submission
        valid_submission = sample_config.submissions[0]  # Get first submission
        schedule = {valid_submission.id: date(2025, 4, 1)}
        start_date = date(2025, 4, 1)
        
        result = validate_submission_constraints(valid_submission, start_date, schedule, sample_config)
        assert result == True  # Function returns boolean
    
    def test_dependency_satisfaction_validation(self, sample_config) -> None:
        """Test dependency satisfaction for submissions."""
        # Use the sample_config fixture which already has submissions with dependencies
        
        # Find a submission that has dependencies
        dependent_submission = next(s for s in sample_config.submissions if s.depends_on)
        
        # Test with dependencies satisfied
        valid_schedule = {
            dependent_submission.depends_on[0]: date(2025, 1, 1),  # Dependency starts first
            dependent_submission.id: date(2025, 3, 1)              # Submission starts after dependency
        }
        start_date = date(2025, 3, 1)
        
        result = validate_submission_constraints(dependent_submission, start_date, valid_schedule, sample_config)
        assert result == True
        
        # Test with dependencies violated
        invalid_schedule = {
            dependent_submission.id: date(2025, 1, 1)  # Submission starts before dependency
        }
        start_date = date(2025, 1, 1)
        
        invalid_result = validate_submission_constraints(dependent_submission, start_date, invalid_schedule, sample_config)
        assert invalid_result == False
    
    def test_venue_compatibility_validation(self, sample_config) -> None:
        """Test venue compatibility for individual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Get a submission and its assigned conference
        submission = next(s for s in sample_config.submissions if s.conference_id)
        conference = next(c for c in sample_config.conferences if c.id == submission.conference_id)
        
        # Test venue compatibility
        schedule = {submission.id: date(2025, 4, 1)}
        start_date = date(2025, 4, 1)
        
        result = validate_submission_constraints(submission, start_date, schedule, sample_config)
        assert result == True
        
        # Test with incompatible venue (this would require modifying the submission)
        # For now, just verify the validation runs
    
    def test_deadline_compliance_validation(self, sample_config) -> None:
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
            valid_schedule = {submission.id: deadline - timedelta(days=30)}  # 30 days before deadline
            start_date = deadline - timedelta(days=30)
            
            result = validate_submission_constraints(submission, start_date, valid_schedule, sample_config)
            assert result == True
            
            # Test with invalid schedule (after deadline)
            invalid_schedule = {submission.id: deadline + timedelta(days=30)}  # 30 days after deadline
            start_date = deadline + timedelta(days=30)
            
            invalid_result = validate_submission_constraints(submission, start_date, invalid_schedule, sample_config)
            assert invalid_result == False
