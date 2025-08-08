"""
Tests for deadline validation module.
"""

import pytest
from datetime import date
from src.validation.deadline import validate_deadline_constraints, validate_deadline_compliance
from src.core.models import Config, Submission, DeadlineValidation


class TestDeadlineValidation:
    """Test cases for deadline validation functions."""
    
    def test_validate_deadline_constraints_empty_schedule(self):
        """Test deadline validation with empty schedule."""
        # Create empty config with required parameters
        config = Config(
            submissions={},
            conferences={},
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        schedule = {}
        
        result = validate_deadline_constraints(schedule, config)
        assert isinstance(result, DeadlineValidation)
        assert result.is_valid == True
        assert result.total_submissions == 0
    
    def test_validate_deadline_compliance_alias(self):
        """Test the backward compatibility alias."""
        # Create empty config with required parameters
        config = Config(
            submissions={},
            conferences={},
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        schedule = {}
        
        result = validate_deadline_compliance(schedule, config)
        assert isinstance(result, DeadlineValidation)
        assert result.is_valid == True
    
    def test_deadline_validation_with_submissions(self):
        """Test deadline validation with actual submissions."""
        # This test would need proper setup with Config and submissions
        pass
    
    def test_blackout_date_validation(self):
        """Test blackout date validation."""
        # Test validation against blackout dates
        pass
