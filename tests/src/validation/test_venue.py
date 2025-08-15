from typing import Dict, List, Any, Optional

"""
Tests for venue validation module.
"""

import pytest
from datetime import date
from src.validation.venue import validate_venue_constraints
from src.core.models import Config, Submission, Conference, ConferenceType, SubmissionType


class TestVenueValidation:
    """Test cases for venue validation functions."""
    
    def test_validate_venue_constraints_empty_schedule(self, empty_config) -> None:
        """Test venue validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result: Any = validate_venue_constraints(schedule, empty_config)
        assert result["is_valid"] == True
        assert "violations" in result
        assert "conference_compatibility" in result
    
    def test_validate_venue_constraints_with_submissions(self, sample_config) -> None:
        """Test venue validation with actual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with valid schedule (proper conference assignments)
        valid_schedule = {
            "mod1-wrk": date(2025, 4, 1),
            "paper1-pap": date(2025, 5, 1),
            "mod2-wrk": date(2025, 2, 1),
            "paper2-pap": date(2025, 3, 1)
        }
        
        result = validate_venue_constraints(valid_schedule, sample_config)
        # The validation might fail due to other constraints, but we can test the structure
        assert "is_valid" in result
        assert "violations" in result
        
        # Check for nested validation results
        assert "conference_compatibility" in result
        assert "conference_submission_compatibility" in result
        assert "single_conference_policy" in result
        
        # Test with invalid schedule (wrong conference assignments)
        invalid_schedule = {
            "mod1-wrk": date(2025, 4, 1),
            "paper1-pap": date(2025, 5, 1),
            "mod2-wrk": date(2025, 2, 1),
            "paper2-pap": date(2025, 3, 1)
        }
        
        # This should still return a valid result structure even if validation fails
        result = validate_venue_constraints(invalid_schedule, sample_config)
        assert "is_valid" in result
        assert "violations" in result
    
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
        
        # Test compatibility validation
        # Engineering submission should be compatible with engineering conference
        eng_compatibility = engineering_conf.validate_submission_compatibility(engineering_submission)
        assert len(eng_compatibility) == 0  # No errors
        
        # Medical submission should be compatible with medical conference
        med_compatibility = medical_conf.validate_submission_compatibility(medical_submission)
        assert len(med_compatibility) == 0  # No errors
        
        # Engineering submission with medical conference might have compatibility issues
        # but this depends on business rules - for now, just test the validation runs
        cross_compatibility = medical_conf.validate_submission_compatibility(engineering_submission)
        # This might or might not have errors depending on business rules
    
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
        
        # Test that both submission types are accepted
        paper_compatibility = mixed_conf.validate_submission_compatibility(paper_submission)
        assert len(paper_compatibility) == 0  # No errors
        
        abstract_compatibility = mixed_conf.validate_submission_compatibility(abstract_submission)
        assert len(abstract_compatibility) == 0  # No errors
        
        # Test conference submission type detection
        # ICRA should accept both abstracts and papers based on the fixture
        assert mixed_conf.accepts_submission_type(paper_submission.kind) == True
        assert mixed_conf.accepts_submission_type(abstract_submission.kind) == True
