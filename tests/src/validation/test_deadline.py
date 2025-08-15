"""
Tests for deadline validation module.
"""

from datetime import date
from typing import Dict, List, Any

import pytest

from src.validation.deadline import validate_deadline_constraints, validate_deadline_compliance
from src.core.models import Config, Submission, DeadlineValidation


class TestDeadlineValidation:
    """Test cases for deadline validation functions."""
    
    def test_validate_deadline_constraints_empty_schedule(self) -> None:
        """Test deadline validation with empty schedule."""
        # Create empty config with required parameters
        config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        schedule: Dict[str, date] = {}
        
        result: DeadlineValidation = validate_deadline_constraints(schedule, config)
        assert isinstance(result, DeadlineValidation)
        assert result.is_valid == True
        assert result.total_submissions == 0
    
    def test_validate_deadline_compliance_alias(self) -> None:
        """Test the backward compatibility alias."""
        # Create empty config with required parameters
        config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        schedule: Dict[str, date] = {}
        
        result: DeadlineValidation = validate_deadline_compliance(schedule, config)
        assert isinstance(result, DeadlineValidation)
        assert result.is_valid == True
    
    def test_deadline_validation_with_submissions(self, sample_config) -> None:
        """Test deadline validation with actual submissions."""
        from src.core.models import SubmissionType, Conference, ConferenceType, ConferenceRecurrence
        
        # Use the sample_config fixture which already has submissions and conferences
        config = sample_config
        
        # Test with valid schedule (submissions before deadlines)
        schedule = {
            "mod1-wrk": date(2025, 4, 1),  # 2 months before ICRA deadline
            "paper1-pap": date(2025, 5, 1), # 1 month before ICRA deadline
            "mod2-wrk": date(2025, 2, 1),  # 1 month before MICCAI deadline
            "paper2-pap": date(2025, 3, 1) # 1 month before MICCAI deadline
        }
        
        result = validate_deadline_constraints(schedule, config)
        assert result.is_valid == True
        assert result.total_submissions == 4
        assert result.compliant_submissions == 4
        assert result.compliance_rate == 100.0  # Percentage format
        
        # Test with invalid schedule (submissions after deadlines)
        invalid_schedule = {
            "mod1-wrk": date(2026, 3, 1),  # After ICRA deadline
            "paper1-pap": date(2026, 4, 1), # After ICRA deadline
            "mod2-wrk": date(2026, 5, 1),  # After MICCAI deadline
            "paper2-pap": date(2026, 6, 1) # After MICCAI deadline
        }
        
        invalid_result = validate_deadline_constraints(invalid_schedule, config)
        assert invalid_result.is_valid == False
        assert len(invalid_result.violations) > 0
    
    def test_blackout_date_validation(self, sample_config) -> None:
        """Test blackout date validation."""
        # Create a config with blackout dates
        config_with_blackouts = Config(
            submissions=sample_config.submissions,
            conferences=sample_config.conferences,
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            blackout_dates=[date(2025, 1, 1), date(2025, 7, 4)]  # New Year's and July 4th
        )
        
        # Test with valid schedule (no blackout dates)
        valid_schedule = {
            "mod1-wrk": date(2025, 4, 15),  # Regular weekday
            "paper1-pap": date(2025, 5, 15)  # Regular weekday
        }
        result = validate_deadline_constraints(valid_schedule, config_with_blackouts)
        assert result.is_valid == True
        
        # Test with invalid schedule (blackout date)
        invalid_schedule = {
            "mod1-wrk": date(2025, 1, 1),  # New Year's Day
            "paper1-pap": date(2025, 5, 15)  # Regular weekday
        }
        invalid_result = validate_deadline_constraints(invalid_schedule, config_with_blackouts)
        assert invalid_result.is_valid == False
        assert len(invalid_result.violations) > 0
