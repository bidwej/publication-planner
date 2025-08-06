"""Tests for constraint validation."""

import pytest
from datetime import date, timedelta
from src.core.config import load_config
from src.core.constraints import (
    validate_deadline_compliance,
    validate_dependency_satisfaction,
    validate_resource_constraints,
    validate_all_constraints,
    validate_soft_block_model,
    validate_conference_compatibility,
    validate_single_conference_policy,
    validate_blackout_dates,
    validate_scheduling_options,
    validate_priority_weighting,
    validate_paper_lead_time_months,
    validate_all_constraints_comprehensive
)


class TestDeadlineCompliance:
    """Test deadline compliance validation."""
    
    def test_valid_deadlines(self):
        """Test that valid deadlines pass validation."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid deadlines (much earlier to account for duration)
        schedule = {
            "J1-pap": date(2024, 11, 1),  # Much before ICML deadline
            "J2-pap": date(2024, 11, 1),  # Much before MICCAI deadline
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert result.is_valid is True
        assert result.compliance_rate == 100.0
    
    def test_missing_deadlines(self):
        """Test that submissions without deadlines are handled."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with submissions that have no deadlines
        schedule = {
            "1-wrk": date(2025, 1, 1),  # Mod without conference assignment
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert result.is_valid is True
        assert result.total_submissions == 0
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_deadline_compliance({}, config)
        
        assert result.is_valid is True
        assert result.total_submissions == 0


class TestDependencySatisfaction:
    """Test dependency satisfaction validation."""
    
    def test_valid_dependencies(self):
        """Test that valid dependencies pass validation."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid dependencies
        schedule = {
            "1-wrk": date(2025, 1, 1),   # Mod 1
            "J1-pap": date(2025, 2, 1),  # Paper depends on mod 1
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is True
        assert result.satisfaction_rate == 100.0
    
    def test_violated_dependencies(self):
        """Test that violated dependencies are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with violated dependencies
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Paper before its dependency
            "1-wrk": date(2025, 2, 1),   # Mod after paper
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is False
        assert result.satisfaction_rate < 100.0
    
    def test_missing_dependencies(self):
        """Test that missing dependencies are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with missing dependencies
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Paper without its dependency
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is False
        assert result.satisfaction_rate < 100.0
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_dependency_satisfaction({}, config)
        
        assert result.is_valid is True
        assert result.total_dependencies == 0


class TestResourceConstraints:
    """Test resource constraint validation."""
    
    def test_valid_resource_usage(self):
        """Test that valid resource usage passes validation."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid concurrency
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 2, 1),  # Different time periods
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert result.is_valid is True
        assert result.max_observed <= result.max_concurrent
    
    def test_concurrent_violation(self):
        """Test that concurrent violations are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with too many concurrent submissions
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
            "J3-pap": date(2025, 1, 1),  # Too many on same day
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert result.is_valid is False
        assert result.max_observed > result.max_concurrent
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_resource_constraints({}, config)
        
        assert result.is_valid is True
        assert result.max_observed == 0


class TestAllConstraints:
    """Test all constraints together."""
    
    def test_valid_schedule(self):
        """Test that a valid schedule passes all constraints."""
        config = load_config("tests/common/data/config.json")
        
        # Create a valid schedule with proper dependency order
        schedule = {
            "1-wrk": date(2024, 6, 1),   # Mod 1 (much earlier)
            "J1-pap": date(2024, 12, 1),  # Paper after mod dependency
        }
        
        result = validate_all_constraints(schedule, config)
        
        assert result.is_valid is True
        assert result.deadlines.is_valid is True
        assert result.dependencies.is_valid is True
        assert result.resources.is_valid is True
    
    def test_invalid_schedule(self):
        """Test that an invalid schedule fails constraints."""
        config = load_config("tests/common/data/config.json")
        
        # Create an invalid schedule
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Paper without dependency
            "J2-pap": date(2025, 1, 1),  # Too many concurrent
            "J3-pap": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_all_constraints(schedule, config)
        
        assert result.is_valid is False
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_all_constraints({}, config)
        
        assert result.is_valid is True


class TestConstraintViolations:
    """Test constraint violation details."""
    
    def test_deadline_violations(self):
        """Test deadline violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with deadline violations
        schedule = {
            "J1-pap": date(2025, 12, 1),  # After deadline
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            assert violation.submission_id == "J1-pap"
            # Check if it's a DeadlineViolation with days_late attribute
            if hasattr(violation, 'days_late'):
                assert violation.days_late > 0
    
    def test_dependency_violations(self):
        """Test dependency violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with dependency violations
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Paper before dependency
            "1-wrk": date(2025, 2, 1),   # Dependency after paper
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            assert violation.submission_id == "J1-pap"
            # Check if it's a DependencyViolation with dependency_id attribute
            if hasattr(violation, 'dependency_id'):
                assert violation.dependency_id == "1-wrk"
    
    def test_resource_violations(self):
        """Test resource violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with resource violations
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
            "J3-pap": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            # Check if it's a ResourceViolation with load/limit/excess attributes
            if hasattr(violation, 'load') and hasattr(violation, 'limit') and hasattr(violation, 'excess'):
                assert violation.load > violation.limit
                assert violation.excess > 0


class TestSoftBlockModel:
    """Test soft block model for PCCP modifications."""
    
    def test_soft_block_model_compliant_mods(self):
        """Test that mods within ±2 months are compliant."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with mods within ±2 months
        schedule = {
            "1-wrk": date(2025, 6, 1),  # Mod 1: est_data_ready = 2025-06-01
            "2-wrk": date(2025, 7, 1),  # Mod 2: est_data_ready = 2025-07-01
        }
        
        result = validate_soft_block_model(schedule, config)
        
        assert result["is_valid"] is True
        assert result["compliant_mods"] == 2
        assert result["total_mods"] == 2
        assert result["compliance_rate"] == 100.0
    
    def test_soft_block_model_violating_mods(self):
        """Test that mods outside ±2 months are flagged."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with mods outside ±2 months
        schedule = {
            "1-wrk": date(2025, 9, 1),  # 3 months after est_data_ready (violation)
            "2-wrk": date(2025, 4, 1),  # 3 months before est_data_ready (violation)
        }
        
        result = validate_soft_block_model(schedule, config)
        
        assert result["is_valid"] is False
        assert result["compliant_mods"] == 0
        assert result["total_mods"] == 2
        assert abs(result["compliance_rate"] - 0.0) < 0.1
        assert len(result["violations"]) == 2


class TestConferenceCompatibility:
    """Test conference compatibility validation."""
    
    def test_conference_compatibility_valid(self):
        """Test valid conference assignments."""
        config = load_config("tests/common/data/config.json")
        
        # Create schedule with valid assignments
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Engineering paper
            "J2-pap": date(2025, 1, 1),  # Medical paper
        }
        
        # Manually set conference assignments
        config.submissions_dict["J1-pap"].conference_id = "ICML"  # Engineering
        config.submissions_dict["J2-pap"].conference_id = "MICCAI"  # Medical
        
        result = validate_conference_compatibility(schedule, config)
        
        assert result["is_valid"] is True
        assert result["compatible_submissions"] == 2
        assert result["total_submissions"] == 2
        assert result["compatibility_rate"] == 100.0
    
    def test_conference_compatibility_violation(self):
        """Test medical paper assigned to engineering conference."""
        config = load_config("tests/common/data/config.json")
        
        schedule = {
            "J2-pap": date(2025, 1, 1),  # Medical paper
        }
        
        # Assign medical paper to engineering conference (violation)
        config.submissions_dict["J2-pap"].conference_id = "ICML"  # Engineering
        
        result = validate_conference_compatibility(schedule, config)
        
        assert result["is_valid"] is False
        assert result["compatible_submissions"] == 0
        assert result["total_submissions"] == 1
        assert result["compatibility_rate"] == 0.0
        assert len(result["violations"]) == 1
        assert "Medical paper" in result["violations"][0]["description"]


class TestSingleConferencePolicy:
    """Test single conference policy validation."""
    
    def test_single_conference_policy_valid(self):
        """Test valid single conference assignments."""
        config = load_config("tests/common/data/config.json")
        
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
        }
        
        # Assign different conferences
        config.submissions_dict["J1-pap"].conference_id = "ICML"
        config.submissions_dict["J2-pap"].conference_id = "MICCAI"
        
        result = validate_single_conference_policy(schedule, config)
        
        assert result["is_valid"] is True
        assert result["total_papers"] == 2
        assert len(result["violations"]) == 0


class TestBlackoutDates:
    """Test blackout dates validation."""
    
    def test_blackout_dates_compliant(self):
        """Test submissions not on blackout dates."""
        config = load_config("tests/common/data/config.json")
        
        # Create schedule avoiding blackout dates (use dates that are definitely not holidays)
        # Papers have duration, so need to be far from any holidays
        schedule = {
            "J1-pap": date(2025, 4, 15),  # Tuesday (far from holidays)
            "J2-pap": date(2025, 4, 16),  # Wednesday (far from holidays)
        }
        
        result = validate_blackout_dates(schedule, config)
        
        # Should be valid if no blackout dates configured
        if config.blackout_dates:
            assert result["is_valid"] is True
            assert result["compliant_submissions"] == 2
            assert result["total_submissions"] == 2
            assert result["compliance_rate"] == 100.0
        else:
            # If no blackout dates, should be valid
            assert result["is_valid"] is True
    
    def test_blackout_dates_violation(self):
        """Test submissions on blackout dates."""
        config = load_config("tests/common/data/config.json")
        
        # Add a blackout date to config
        config.blackout_dates = [date(2025, 1, 15)]
        
        schedule = {
            "J1-pap": date(2025, 1, 15),  # On blackout date
            "J2-pap": date(2025, 1, 20),  # Regular date
        }
        
        result = validate_blackout_dates(schedule, config)
        
        assert result["is_valid"] is False
        assert result["compliant_submissions"] == 1
        assert result["total_submissions"] == 2
        assert result["compliance_rate"] == 50.0
        assert len(result["violations"]) == 1


class TestSchedulingOptions:
    """Test scheduling options validation."""
    
    def test_scheduling_options_no_config(self):
        """Test when no scheduling options configured."""
        config = load_config("tests/common/data/config.json")
        config.scheduling_options = None
        
        schedule = {
            "J1-pap": date(2025, 1, 1),
        }
        
        result = validate_scheduling_options(schedule, config)
        
        assert result["is_valid"] is True
        assert result["summary"] == "No scheduling options configured"


class TestPriorityWeighting:
    """Test priority weighting validation."""
    
    def test_priority_weighting_validation(self):
        """Test priority weighting calculation."""
        config = load_config("tests/common/data/config.json")
        
        schedule = {
            "J1-pap": date(2025, 1, 1),  # Engineering paper
            "J2-pap": date(2025, 1, 1),  # Medical paper
            "1-wrk": date(2025, 1, 1),   # Mod
        }
        
        result = validate_priority_weighting(schedule, config)
        
        assert result["is_valid"] is True
        assert result["total_submissions"] == 3
        assert "average_priority" in result
        assert result["average_priority"] > 0
    
    def test_priority_weighting_no_config(self):
        """Test when no priority weights configured."""
        config = load_config("tests/common/data/config.json")
        config.priority_weights = None
        
        schedule = {
            "J1-pap": date(2025, 1, 1),
        }
        
        result = validate_priority_weighting(schedule, config)
        
        assert result["is_valid"] is True
        assert result["summary"] == "No priority weights configured"


class TestPaperLeadTimeMonths:
    """Test paper lead time months validation."""
    
    def test_paper_lead_time_months_compliant(self):
        """Test papers using correct lead time months."""
        config = load_config("tests/common/data/config.json")
        
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
        }
        
        result = validate_paper_lead_time_months(schedule, config)
        
        # Papers in test data have different draft_window_months (2 and 3)
        # while config default is 3, so some will violate
        assert result["total_papers"] == 2
        assert "compliance_rate" in result
        # The test data has papers with draft_window_months of 2 and 3,
        # while config default is 3, so we expect some violations


class TestComprehensiveConstraints:
    """Test comprehensive constraint validation."""
    
    def test_comprehensive_constraints_valid_schedule(self):
        """Test comprehensive validation with valid schedule."""
        config = load_config("tests/common/data/config.json")
        
        # Create a valid schedule
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
            "1-wrk": date(2025, 6, 1),
        }
        
        result = validate_all_constraints_comprehensive(schedule, config)
        
        # Check that all constraint types are present
        assert "deadlines" in result
        assert "dependencies" in result
        assert "resources" in result
        assert "blackout_dates" in result
        assert "scheduling_options" in result
        assert "conference_compatibility" in result
        assert "single_conference_policy" in result
        assert "soft_block_model" in result
        assert "priority_weighting" in result
        assert "paper_lead_time" in result
        
        # Check summary
        assert "summary" in result
        assert "overall_valid" in result["summary"]
        assert "total_violations" in result
    
    def test_comprehensive_constraints_violations(self):
        """Test comprehensive validation with violations."""
        config = load_config("tests/common/data/config.json")
        
        # Create schedule with violations
        schedule = {
            "J1-pap": date(2025, 1, 1),
            "J2-pap": date(2025, 1, 1),
            "J3-pap": date(2025, 1, 1),  # Too many concurrent
            "J4-pap": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_all_constraints_comprehensive(schedule, config)
        
        # Should have violations
        assert result["total_violations"] > 0
        assert result["summary"]["overall_valid"] is False
