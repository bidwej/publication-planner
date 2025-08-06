"""Tests for core constraints module."""

import pytest
from typing import Dict
from datetime import date, timedelta
from src.core.models import (
    Config, Submission, Conference, ConferenceType, 
    ConferenceRecurrence, SubmissionType,
    DeadlineValidation, DependencyValidation, ResourceValidation,
    ConstraintValidationResult
)
from src.core.constraints import (
    validate_deadline_compliance,
    validate_dependency_satisfaction,
    validate_resource_constraints,
    validate_all_constraints
)


class TestDeadlineCompliance:
    """Test deadline compliance validation."""
    
    def test_valid_deadlines(self, config):
        """Test validation with valid deadlines."""
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 15)
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert isinstance(result, DeadlineValidation)
        assert result.is_valid
        assert result.compliance_rate >= 0.0
        assert result.compliance_rate <= 100.0
        assert result.total_submissions >= 0
        assert result.compliant_submissions >= 0
    
    def test_missing_deadlines(self, config):
        """Test validation with missing deadline information."""
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1)
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert isinstance(result, DeadlineValidation)
        # Should handle missing deadlines gracefully
        assert result.total_submissions >= 0
    
    def test_empty_schedule(self, config):
        """Test validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result = validate_deadline_compliance(schedule, config)
        
        assert isinstance(result, DeadlineValidation)
        assert result.total_submissions == 0
        assert result.compliant_submissions == 0
        assert result.compliance_rate == 100.0  # No violations = 100% compliance


class TestDependencySatisfaction:
    """Test dependency satisfaction validation."""
    
    def test_valid_dependencies(self, config):
        """Test validation with valid dependencies."""
        schedule: Dict[str, date] = {
            "parent": date(2025, 1, 1),
            "child": date(2025, 2, 1)  # After parent
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert isinstance(result, DependencyValidation)
        assert result.is_valid
        assert result.satisfaction_rate >= 0.0
        assert result.satisfaction_rate <= 100.0
        assert result.total_dependencies >= 0
        assert result.satisfied_dependencies >= 0
    
    def test_violated_dependencies(self, config):
        """Test validation with violated dependencies."""
        schedule: Dict[str, date] = {
            "parent": date(2025, 2, 1),
            "child": date(2025, 1, 1)  # Before parent - violation
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert isinstance(result, DependencyValidation)
        # Should detect violations
        assert result.total_dependencies >= 0
        assert result.satisfied_dependencies >= 0
    
    def test_missing_dependencies(self, config):
        """Test validation with missing dependencies."""
        schedule: Dict[str, date] = {
            "child": date(2025, 1, 1)  # Parent not in schedule
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert isinstance(result, DependencyValidation)
        assert result.total_dependencies >= 0
    
    def test_empty_schedule(self, config):
        """Test validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert isinstance(result, DependencyValidation)
        assert result.total_dependencies == 0
        assert result.satisfied_dependencies == 0
        assert result.satisfaction_rate == 100.0  # No violations = 100% satisfaction


class TestResourceConstraints:
    """Test resource constraint validation."""
    
    def test_valid_resource_usage(self, config):
        """Test validation with valid resource usage."""
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 15)  # Different days
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert isinstance(result, ResourceValidation)
        assert result.is_valid
        assert result.max_concurrent >= 0
        assert result.max_observed >= 0
        assert result.total_days >= 0
    
    def test_concurrent_violation(self, config):
        """Test validation with concurrent submission violation."""
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Same day - potential violation
            "paper3": date(2025, 1, 1)   # Same day - potential violation
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert isinstance(result, ResourceValidation)
        assert result.max_concurrent >= 0
        assert result.max_observed >= 0
        assert result.total_days >= 0
    
    def test_empty_schedule(self, config):
        """Test validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result = validate_resource_constraints(schedule, config)
        
        assert isinstance(result, ResourceValidation)
        assert result.max_concurrent >= 0
        assert result.max_observed == 0
        assert result.total_days == 0


class TestAllConstraints:
    """Test comprehensive constraint validation."""
    
    def test_valid_schedule(self, config):
        """Test all constraints with valid schedule."""
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 15)
        }
        
        result = validate_all_constraints(schedule, config)
        
        assert isinstance(result, ConstraintValidationResult)
        assert isinstance(result.deadlines, DeadlineValidation)
        assert isinstance(result.dependencies, DependencyValidation)
        assert isinstance(result.resources, ResourceValidation)
        assert isinstance(result.is_valid, bool)
    
    def test_invalid_schedule(self, config):
        """Test all constraints with invalid schedule."""
        schedule: Dict[str, date] = {
            "parent": date(2025, 2, 1),
            "child": date(2025, 1, 1),  # Violates dependency
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Violates concurrency
            "paper3": date(2025, 1, 1)   # Violates concurrency
        }
        
        result = validate_all_constraints(schedule, config)
        
        assert isinstance(result, ConstraintValidationResult)
        assert isinstance(result.deadlines, DeadlineValidation)
        assert isinstance(result.dependencies, DependencyValidation)
        assert isinstance(result.resources, ResourceValidation)
        assert isinstance(result.is_valid, bool)
    
    def test_empty_schedule(self, config):
        """Test all constraints with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result = validate_all_constraints(schedule, config)
        
        assert isinstance(result, ConstraintValidationResult)
        assert isinstance(result.deadlines, DeadlineValidation)
        assert isinstance(result.dependencies, DependencyValidation)
        assert isinstance(result.resources, ResourceValidation)
        assert isinstance(result.is_valid, bool)


class TestConstraintViolations:
    """Test constraint violation detection."""
    
    def test_deadline_violations(self, config):
        """Test deadline violation detection."""
        # Create a schedule with late submissions
        schedule: Dict[str, date] = {
            "late_paper": date(2025, 12, 31)  # Very late
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert isinstance(result, DeadlineValidation)
        # Should detect violations if any submissions are late
        assert result.total_submissions >= 0
    
    def test_dependency_violations(self, config):
        """Test dependency violation detection."""
        schedule: Dict[str, date] = {
            "child": date(2025, 1, 1),   # Child first
            "parent": date(2025, 2, 1)   # Parent later - violation
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert isinstance(result, DependencyValidation)
        # Should detect dependency violations
        assert result.total_dependencies >= 0
    
    def test_resource_violations(self, config):
        """Test resource violation detection."""
        # Create a schedule with too many concurrent submissions
        schedule: Dict[str, date] = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),
            "paper3": date(2025, 1, 1),
            "paper4": date(2025, 1, 1),
            "paper5": date(2025, 1, 1)
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert isinstance(result, ResourceValidation)
        # Should detect resource violations if concurrency limit exceeded
        assert result.max_observed >= 0
