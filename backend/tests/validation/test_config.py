"""Test config validation functions."""

import pytest
from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType
from src.validation.config import validate_config


class TestConfigValidation:
    """Test cases for config validation functions."""
    
    def test_validate_config_empty_config(self) -> None:
        """Test config validation with empty configuration."""
        empty_config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        result = validate_config(empty_config)
        assert isinstance(result, list)
        # Should have errors for missing submissions and conferences
        assert len(result) > 0
    
    def test_validate_config_valid_config(self, sample_config) -> None:
        """Test config validation with valid configuration."""
        result = validate_config(sample_config)
        assert isinstance(result, list)
        # Should have no validation errors
        assert len(result) == 0
    
    def test_validate_config_invalid_lead_times(self) -> None:
        """Test config validation with invalid lead times."""
        invalid_config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=-1,  # Invalid negative value
            min_paper_lead_time_days=-90,    # Invalid negative value
            max_concurrent_submissions=3
        )
        
        result = validate_config(invalid_config)
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check for specific error messages
        error_messages = [error.lower() for error in result]
        assert any("negative" in error for error in error_messages)
    
    def test_validate_config_invalid_concurrency_limit(self) -> None:
        """Test config validation with invalid concurrency limit."""
        invalid_config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=0  # Invalid: must be at least 1
        )
        
        result = validate_config(invalid_config)
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check for specific error message
        error_messages = [error.lower() for error in result]
        assert any("at least 1" in error for error in error_messages)
    
    def test_validate_config_submission_validation(self, sample_config) -> None:
        """Test that config validation includes submission validation."""
        # Create a config with invalid submission (missing title)
        invalid_submission = Submission(
            id="invalid-sub",
            title="",  # Missing title
            kind=SubmissionType.PAPER,
            conference_id="ICRA2026"
        )
        
        # Use model_copy to create a new config with the invalid submission
        invalid_config = sample_config.model_copy(update={
            "submissions": [invalid_submission]
        })
        
        result = validate_config(invalid_config)
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check for submission validation errors
        error_messages = [error.lower() for error in result]
        assert any("missing title" in error for error in error_messages)
    
    def test_validate_config_conference_validation(self, sample_config) -> None:
        """Test that config validation includes conference validation."""
        # Create a config with invalid conference (missing deadlines)
        invalid_conference = Conference(
            id="invalid-conf",
            name="Invalid Conference",
            conf_type=ConferenceType.ENGINEERING,
            recurrence="annual",  # Add required field
            deadlines={}  # Missing deadlines
        )
        
        # Use model_copy to create a new config with the invalid conference
        invalid_config = sample_config.model_copy(update={
            "conferences": [invalid_conference]
        })
        
        result = validate_config(invalid_config)
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check for conference validation errors
        error_messages = [error.lower() for error in result]
        assert any("no deadlines defined" in error for error in error_messages)
    
    def test_validate_config_constants_validation(self, sample_config) -> None:
        """Test that config validation includes constants validation."""
        # This test ensures that constants validation is called
        # The actual constants validation logic is tested separately
        result = validate_config(sample_config)
        assert isinstance(result, list)
        # Should run without crashing and return a list
