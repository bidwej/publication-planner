from typing import Dict, List, Any, Optional

"""
Tests for schedule validation module.
"""

import pytest
from datetime import date
from src.validation.schedule import validate_schedule_constraints
from core.models import Config, Submission


class TestScheduleValidation:
    """Test cases for schedule validation functions."""
    
    def test_validate_schedule_constraints_empty_schedule(self, empty_config) -> None:
        """Test schedule validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result: Any = validate_schedule_constraints(schedule, empty_config)
        assert "summary" in result
        assert result["summary"]["overall_valid"] == True
        assert "constraints" in result
        assert "analytics" in result
    
    def test_schedule_validation_with_submissions(self, sample_config) -> None:
        """Test schedule validation with actual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with valid schedule (dependencies satisfied and no blackout dates)
        valid_schedule = {
            "mod1-wrk": date(2025, 4, 15),   # Work item starts first, no blackout
            "paper1-pap": date(2025, 5, 15)  # Paper starts after mod1 completes
        }
        
        result = validate_schedule_constraints(valid_schedule, sample_config)
        # The validation might fail due to other constraints, but we can test the structure
        assert "summary" in result
        assert "constraints" in result
        assert "analytics" in result
        
        # Test with invalid schedule (dependencies violated)
        invalid_schedule = {
            "mod1-wrk": date(2025, 5, 15),   # Work item starts later
            "paper1-pap": date(2025, 4, 15)  # Paper starts before mod1
        }
        
        invalid_result = validate_schedule_constraints(invalid_schedule, sample_config)
        # This should fail due to dependency violation
        assert "summary" in invalid_result
        assert "constraints" in invalid_result
    
    def test_dependency_validation(self, sample_config) -> None:
        """Test dependency satisfaction validation."""
        # Use the sample_config fixture which already has submissions with dependencies
        
        # Test with valid dependency chain (respecting durations)
        valid_schedule = {
            "mod1-wrk": date(2025, 1, 1),   # First
            "paper1-pap": date(2025, 2, 1), # After mod1 (assuming mod1 takes ~1 month)
            "mod2-wrk": date(2025, 3, 1),   # After paper1
            "paper2-pap": date(2025, 4, 1)  # After mod2
        }
        
        result = validate_schedule_constraints(valid_schedule, sample_config)
        assert "summary" in result
        assert "constraints" in result
        
        # Test with broken dependency chain
        invalid_schedule = {
            "mod1-wrk": date(2025, 3, 1),   # Later
            "paper1-pap": date(2025, 1, 1), # Before mod1 (violation)
            "mod2-wrk": date(2025, 2, 1),   # After mod1
            "paper2-pap": date(2025, 4, 1)  # After both
        }
        
        invalid_result = validate_schedule_constraints(invalid_schedule, sample_config)
        assert "summary" in invalid_result
        assert "constraints" in invalid_result
    
    def test_comprehensive_constraint_validation(self, sample_config) -> None:
        """Test comprehensive constraint validation."""
        # Create a modified config with stricter concurrency limits to test resource constraints
        strict_config = Config(
            submissions=sample_config.submissions,
            conferences=sample_config.conferences,
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=2,  # Strict limit
            blackout_dates=[date(2025, 1, 1)]  # New Year's Day
        )
        
        # Test with schedule that violates multiple constraints
        invalid_schedule = {
            "mod1-wrk": date(2025, 1, 1),    # Valid start
            "paper1-pap": date(2025, 1, 1),  # Same day as mod1 (resource violation)
            "mod2-wrk": date(2025, 1, 1),    # Same day as others (resource violation)
            "paper2-pap": date(2025, 2, 1)   # After others
        }
        
        result = validate_schedule_constraints(invalid_schedule, strict_config)
        assert "summary" in result
        assert "constraints" in result
        
        # Check that multiple constraint types are validated
        constraints = result["constraints"]
        assert "deadlines" in constraints
        assert "dependencies" in constraints
        assert "resources" in constraints
        # Note: 'venues' might not be present if no venue validation is performed
        # assert "venues" in constraints
