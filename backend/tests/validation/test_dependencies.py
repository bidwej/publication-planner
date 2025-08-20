"""Test dependency validation functions."""

import pytest
from datetime import date
from core.models import Config, Submission, Schedule, SubmissionType, ValidationResult
from validation.dependencies import validate_dependency_constraints


class TestDependenciesValidation:
    """Test cases for dependency validation functions."""
    
    def test_validate_dependency_constraints_empty_schedule(self, empty_config) -> None:
        """Test dependency validation with empty schedule."""
        schedule = Schedule()
        
        result = validate_dependency_constraints(schedule, empty_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("total_dependencies", 0) == 0
    
    def test_validate_dependency_constraints_with_submissions(self, sample_config) -> None:
        """Test dependency validation with actual submissions."""
        # Create a valid schedule with dependencies satisfied
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)
        valid_schedule.add_interval("paper1-pap", date(2025, 2, 1), duration_days=45)  # After mod1
        
        result = validate_dependency_constraints(valid_schedule, sample_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
    
    def test_validate_dependency_constraints_violations(self, sample_config) -> None:
        """Test dependency validation with violations."""
        # Create an invalid schedule with dependencies violated
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=45)  # Before mod1
        invalid_schedule.add_interval("mod1-wrk", date(2025, 2, 1), duration_days=30)   # After paper1
        
        result = validate_dependency_constraints(invalid_schedule, sample_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.violations) > 0
    
    def test_validate_dependency_constraints_missing_dependencies(self, sample_config) -> None:
        """Test dependency validation with missing dependencies."""
        # Create a schedule with missing dependencies
        incomplete_schedule = Schedule()
        incomplete_schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=45)  # mod1-wrk not scheduled
        
        result = validate_dependency_constraints(incomplete_schedule, sample_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.violations) > 0
    
    def test_validate_dependency_constraints_abstract_paper_dependencies(self, sample_config) -> None:
        """Test abstract-paper dependency validation."""
        # Create a schedule with abstract-paper dependencies
        schedule = Schedule()
        schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)
        schedule.add_interval("paper1-pap", date(2025, 2, 1), duration_days=45)  # After mod1
        
        result = validate_dependency_constraints(schedule, sample_config)
        assert isinstance(result, ValidationResult)
        # The validation should run without crashing
        assert isinstance(result.violations, list)
        assert isinstance(result.metadata, dict)
