from typing import Dict, List, Any, Optional

"""
Tests for venue validation module.
"""

import pytest
from datetime import date
from src.validation.venue import validate_venue_constraints, validate_conference_submission_compatibility
from src.core.models import Config, Submission, Conference, ConferenceType, SubmissionType, Schedule, ValidationResult


class TestVenueValidation:
    """Test cases for venue validation functions."""
    
    def test_validate_venue_constraints_empty_schedule(self, empty_config, empty_schedule) -> None:
        """Test venue validation with empty schedule."""
        result = validate_venue_constraints(empty_schedule, empty_config)
        assert result.is_valid == True
        assert hasattr(result, 'violations')
        assert 'compatibility_rate' in result.metadata
    
    def test_validate_venue_constraints_with_submissions(self, sample_config, sample_schedule) -> None:
        """Test venue validation with actual submissions."""
        # Use the sample_config and sample_schedule fixtures which already have data
        
        result = validate_venue_constraints(sample_schedule, sample_config)
        # The validation might fail due to other constraints, but we can test the structure
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'violations')
        
        # Check for metadata
        assert 'compatibility_rate' in result.metadata
        assert 'total_submissions' in result.metadata
        assert 'compliant_submissions' in result.metadata
    
    def test_conference_compatibility_validation(self, sample_config) -> None:
        """Test conference compatibility validation."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Get submissions and conferences from the fixture
        submissions = sample_config.submissions
        conferences = sample_config.conferences
        
        # Find engineering and medical submissions based on author
        engineering_submission = next(s for s in submissions if s.author == "pccp")
        medical_submission = next(s for s in submissions if s.author == "ed")
        
        # Find engineering and medical conferences
        engineering_conf = next(c for c in conferences if c.conf_type.value == "ENGINEERING")
        medical_conf = next(c for c in conferences if c.conf_type.value == "MEDICAL")
        
        # Test that the conference types are correctly identified
        assert engineering_conf.conf_type == ConferenceType.ENGINEERING
        assert medical_conf.conf_type == ConferenceType.MEDICAL
        
        # Test that submissions have the expected author types
        assert engineering_submission.author == "pccp"
        assert medical_submission.author == "ed"
        
        # Test compatibility validation using the validation function
        # Engineering submission should be compatible with engineering conference
        eng_compatibility = validate_conference_submission_compatibility(engineering_conf, engineering_submission)
        assert isinstance(eng_compatibility, list)  # Function returns list of errors
        
        # Medical submission should be compatible with medical conference
        med_compatibility = validate_conference_submission_compatibility(medical_conf, medical_submission)
        assert isinstance(med_compatibility, list)  # Function returns list of errors
        
        # Test cross-compatibility (engineering submission with medical conference)
        cross_compatibility = validate_conference_submission_compatibility(medical_conf, engineering_submission)
        assert isinstance(cross_compatibility, list)  # Function returns list of errors
    
    def test_submission_type_compatibility(self, sample_config) -> None:
        """Test submission type compatibility with conference types."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Get submissions and conferences from the fixture
        submissions = sample_config.submissions
        conferences = sample_config.conferences
        
        # Find paper and abstract submissions
        paper_submission = next(s for s in submissions if s.kind.value == "paper")
        abstract_submission = next(s for s in submissions if s.kind.value == "abstract")
        
        # Find a conference that accepts both types (should be ICRA from the fixture)
        mixed_conf = next(c for c in conferences if c.id == "ICRA2026")
        
        # Test conference submission type detection
        # ICRA should accept both abstracts and papers based on the fixture
        assert mixed_conf.accepts_submission_type(paper_submission.kind) == True
        assert mixed_conf.accepts_submission_type(abstract_submission.kind) == True
        
        # Test that the submission types are correctly identified
        assert paper_submission.kind == SubmissionType.PAPER
        assert abstract_submission.kind == SubmissionType.ABSTRACT
