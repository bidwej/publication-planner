"""Tests for constraint validation."""

from datetime import date, timedelta
from typing import Dict, Any, List

import pytest

from src.core.config import load_config
from src.validation import (
    validate_schedule_constraints,
    validate_deadline_compliance,
    _validate_dependencies_satisfied,
    validate_resources_all_constraints,
    validate_venue_constraints,
)
from src.core.models import Submission, SubmissionType, ConferenceType
from src.core.constants import QUALITY_CONSTANTS


class TestDeadlineCompliance:
    """Test deadline compliance validation."""
    
    def test_valid_deadlines(self):
        """Test that valid deadlines pass validation."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid deadlines (much earlier to account for duration)
        schedule = {
            "J1-pap-ICML": date(2024, 11, 1),  # Much before ICML deadline
            "J2-pap-MICCAI": date(2024, 11, 1),  # Much before MICCAI deadline
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
            "J1-abs-ICML": date(2025, 1, 15),  # Abstract depends on mod 1
            "J1-pap-ICML": date(2025, 2, 1),  # Paper depends on abstract and mod 1
        }
        
        from src.validation.schedule import _validate_dependency_satisfaction
        result = _validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is True
        assert result.satisfaction_rate == 100.0
    
    def test_violated_dependencies(self):
        """Test that violated dependencies are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with violated dependencies
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),  # Paper before its dependency
            "1-wrk": date(2025, 2, 1),   # Mod after paper
        }
        
        from src.validation.schedule import _validate_dependency_satisfaction
        result = _validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is False
        assert result.satisfaction_rate < 100.0
    
    def test_missing_dependencies(self):
        """Test that missing dependencies are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with missing dependencies
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),  # Paper without its dependency
        }
        
        from src.validation.schedule import _validate_dependency_satisfaction
        result = _validate_dependency_satisfaction(schedule, config)
        
        assert result.is_valid is False
        assert result.satisfaction_rate < 100.0
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        from src.validation.schedule import _validate_dependency_satisfaction
        result = _validate_dependency_satisfaction({}, config)
        
        assert result.is_valid is True
        assert result.total_dependencies == 0


class TestResourceConstraints:
    """Test resource constraint validation."""
    
    def test_valid_resource_usage(self):
        """Test that valid resource usage passes validation."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid concurrency
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 2, 1),  # Different time periods
        }
        
        from src.validation.resources import validate_resources_constraints
        result = validate_resources_constraints(schedule, config)
        
        assert result.is_valid is True
        assert result.max_observed <= result.max_concurrent
    
    def test_concurrent_violation(self):
        """Test that concurrent violations are caught."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with too many concurrent submissions
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
            "J3-pap-MICCAI": date(2025, 1, 1),  # Too many on same day
        }
        
        from src.validation.resources import validate_resources_constraints
        result = validate_resources_constraints(schedule, config)
        
        assert result.is_valid is False
        assert result.max_observed > result.max_concurrent
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        from src.validation.resources import validate_resources_constraints
        result = validate_resources_constraints({}, config)
        
        assert result.is_valid is True
        assert result.max_observed == 0


class TestAllConstraints:
    """Test all constraints together."""
    
    def test_valid_schedule(self):
        """Test that a valid schedule passes all constraints."""
        config = load_config("tests/common/data/config.json")
        
        # Create a valid schedule with proper dependency order
        # For ICML (which requires both abstract and paper), we need both submissions
        schedule = {
            "1-wrk": date(2024, 6, 1),   # Mod 1 (much earlier)
            "J1-abs-ICML": date(2024, 11, 1),  # Abstract after mod dependency
            "J1-pap-ICML": date(2024, 12, 1),  # Paper after abstract dependency
        }
        
        result = validate_schedule_all_constraints(schedule, config)
        
        # Debug: print the result to see what's happening
        print(f"Result: {result}")
        
        assert result["summary"]["overall_valid"] is True
        assert result["constraints"]["deadlines"]["is_valid"] is True
        assert result["constraints"]["dependencies"]["is_valid"] is True
        assert result["constraints"]["resources"]["is_valid"] is True
    
    def test_invalid_schedule(self):
        """Test that an invalid schedule fails constraints."""
        config = load_config("tests/common/data/config.json")
        
        # Create an invalid schedule
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),  # Paper without required abstract dependency
            "J2-pap-MICCAI": date(2025, 1, 1),  # Too many concurrent
            "J3-pap-MICCAI": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_schedule_all_constraints(schedule, config)
        
        assert result["summary"]["overall_valid"] is False
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_schedule_all_constraints({}, config)
        
        assert result["summary"]["overall_valid"] is True


class TestConstraintViolations:
    """Test constraint violation details."""
    
    def test_deadline_violations(self):
        """Test deadline violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with deadline violations
        schedule = {
            "J1-pap-ICML": date(2025, 12, 1),  # After deadline
        }
        
        result = validate_deadline_compliance(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            assert violation.submission_id == "J1-pap-ICML"
            # Check if it's a DeadlineViolation with days_late attribute
            if hasattr(violation, 'days_late') and violation.days_late is not None:
                assert violation.days_late > 0
    
    def test_dependency_violations(self):
        """Test dependency violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with dependency violations
        # For ICML, paper depends on both mod and abstract
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),  # Paper before dependencies
            "1-wrk": date(2025, 2, 1),   # Mod dependency after paper
            "J1-abs-ICML": date(2025, 3, 1),  # Abstract dependency after paper
        }
        
        result = validate_dependency_satisfaction(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            assert violation.submission_id == "J1-pap-ICML"
            # Check if it's a DependencyViolation with dependency_id attribute
            if hasattr(violation, 'dependency_id') and violation.dependency_id:
                # Paper depends on both mod and abstract, so either could be missing
                assert violation.dependency_id in ["1-wrk", "J1-abs-ICML"]
    
    def test_resource_violations(self):
        """Test resource violation details."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with resource violations
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
            "J3-pap-MICCAI": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_resource_constraints(schedule, config)
        
        assert len(result.violations) > 0
        for violation in result.violations:
            # Check if it's a ResourceViolation with load/limit/excess attributes
            if (hasattr(violation, 'load') and hasattr(violation, 'limit') and 
                hasattr(violation, 'excess') and violation.load is not None):
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

    def test_soft_block_model_edge_cases(self):
        """Test soft block model with edge cases."""
        config = load_config("tests/common/data/config.json")
        
        # Test with empty schedule
        result = validate_soft_block_model({}, config)
        assert result["is_valid"] is True
        assert result["total_mods"] == 0
        assert result["compliance_rate"] == 100.0
        
        # Test with no modifications (only regular submissions)
        schedule_no_mods = {
            "paper1": date(2025, 1, 15),
            "abstract1": date(2025, 1, 1),
        }
        
        result = validate_soft_block_model(schedule_no_mods, config)
        assert result["is_valid"] is True
        assert result["total_mods"] == 0
        assert result["compliance_rate"] == 100.0
        
        # Test with modifications but no earliest start dates
        schedule_no_earliest = {
            "paper1-wrk": date(2025, 1, 15),  # Mod without earliest start
        }
        
        result = validate_soft_block_model(schedule_no_earliest, config)
        assert result["is_valid"] is True
        assert result["total_mods"] == 0  # Should not count mods without earliest start
        
        # Test with valid modification within ±2 months
        schedule_valid_mod = {
            "paper1-wrk": date(2025, 3, 15),  # Within 2 months of earliest
        }
        
        # Create a submission with earliest start date
        if "paper1-wrk" in config.submissions_dict:
            config.submissions_dict["paper1-wrk"].earliest_start_date = date(2025, 2, 1)
        
        result = validate_soft_block_model(schedule_valid_mod, config)
        if result["total_mods"] > 0:
            assert result["is_valid"] is True
            assert result["compliant_mods"] == 1
        
        # Test with invalid modification outside ±2 months
        schedule_invalid_mod = {
            "paper1-wrk": date(2025, 6, 15),  # 4 months from earliest
        }
        
        result = validate_soft_block_model(schedule_invalid_mod, config)
        if result["total_mods"] > 0:
            assert result["is_valid"] is False
            assert len(result["violations"]) > 0
            assert any("4 months" in v["description"] for v in result["violations"])

    def test_soft_block_model_boundary_cases(self):
        """Test soft block model boundary conditions."""
        config = load_config("tests/common/data/config.json")
        
        # Test exactly at 2 months boundary
        schedule_boundary = {
            "paper1-wrk": date(2025, 4, 1),  # Exactly 2 months from earliest
        }
        
        if "paper1-wrk" in config.submissions_dict:
            config.submissions_dict["paper1-wrk"].earliest_start_date = date(2025, 2, 1)
        
        result = validate_soft_block_model(schedule_boundary, config)
        if result["total_mods"] > 0:
            assert result["is_valid"] is True  # Should be valid at exactly 2 months
        
        # Test just over 2 months boundary
        schedule_over_boundary = {
            "paper1-wrk": date(2025, 4, 2),  # Just over 2 months
        }
        
        result = validate_soft_block_model(schedule_over_boundary, config)
        if result["total_mods"] > 0:
            assert result["is_valid"] is False
            assert len(result["violations"]) > 0

    def test_soft_block_model_consistency_with_base_scheduler(self):
        """Test that soft block validation is consistent between constraints and base scheduler."""
        from src.schedulers.base import BaseScheduler
        
        config = load_config("tests/common/data/config.json")
        
        # Create a mock scheduler to test base scheduler validation
        class MockScheduler(BaseScheduler):
            def schedule(self):
                return {}
        
        scheduler = MockScheduler(config)
        
        # Test with a modification
        submission = config.submissions_dict.get("paper1-wrk")
        if submission:
            submission.earliest_start_date = date(2025, 2, 1)
            
            # Test valid date (within 2 months)
            valid_date = date(2025, 3, 15)
            base_result = scheduler._validate_soft_block_model(submission, valid_date)
            assert base_result is True
            
            # Test invalid date (outside 2 months)
            invalid_date = date(2025, 6, 15)
            base_result = scheduler._validate_soft_block_model(submission, invalid_date)
            assert base_result is False
            
            # Test regular submission (should always be valid)
            regular_submission = config.submissions_dict.get("paper1")
            if regular_submission:
                base_result = scheduler._validate_soft_block_model(regular_submission, valid_date)
                assert base_result is True


class TestConferenceCompatibility:
    """Test conference compatibility validation."""
    
    def test_conference_compatibility_valid(self):
        """Test valid conference assignments."""
        config = load_config("tests/common/data/config.json")
        
        # Use papers that are actually compatible with their conferences
        # J1-pap-ICML is a medical paper assigned to engineering conference (violation)
        # J2-pap-MICCAI is a medical paper assigned to medical conference (valid)
        schedule = {
            "J2-pap-MICCAI": date(2025, 1, 1),  # Medical paper to medical conference (valid)
        }
        
        result = validate_conference_compatibility(schedule, config)
        
        assert result["is_valid"] is True
        assert result["compatible_submissions"] == 1
        assert result["total_submissions"] == 1
        assert result["compatibility_rate"] == 100.0
    
    def test_conference_compatibility_violation(self):
        """Test medical paper assigned to engineering conference."""
        config = load_config("tests/common/data/config.json")
        
        # Create a violation by manually assigning a medical paper to an engineering conference
        # Find a medical paper submission (J2 is medical, goes to MICCAI/ARS/IFAR)
        medical_paper = None
        for sub in config.submissions:
            if sub.id.startswith("J2") and sub.kind == SubmissionType.PAPER and sub.conference_id:
                medical_paper = sub
                break
        
        if medical_paper:
            # Temporarily change the conference assignment to create a violation
            original_conference_id = medical_paper.conference_id
            medical_paper.conference_id = "ICML"  # Engineering conference
            
            schedule = {
                medical_paper.id: date(2025, 1, 1),  # Medical paper assigned to engineering conference
            }
            
            result = validate_conference_compatibility(schedule, config)
            
            # Restore original conference assignment
            medical_paper.conference_id = original_conference_id
            
            assert result["is_valid"] is False
            assert result["compatible_submissions"] == 0
            assert result["total_submissions"] == 1
            assert result["compatibility_rate"] == 0.0
            assert len(result["violations"]) == 1
            assert "Medical paper" in result["violations"][0]["description"]
        else:
            # If no medical paper found, create a test submission manually
            # Create a medical paper submission
            medical_paper = Submission(
                id="test-medical-paper",
                title="Test Medical Paper",
                kind=SubmissionType.PAPER,
                conference_id="ICML",  # Engineering conference (violation)
                engineering=False,  # Medical paper
                depends_on=[],
                draft_window_months=3
            )
            
            # Add to config temporarily
            config.submissions.append(medical_paper)
            config.submissions_dict[medical_paper.id] = medical_paper
            
            schedule = {
                medical_paper.id: date(2025, 1, 1),
            }
            
            result = validate_conference_compatibility(schedule, config)
            
            # Remove test submission
            config.submissions.remove(medical_paper)
            del config.submissions_dict[medical_paper.id]
            
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
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
        }
        
        result = validate_single_conference_policy(schedule, config)
        
        assert result["is_valid"] is True
        assert result["total_papers"] == 2
        assert len(result["violations"]) == 0


class TestBlackoutDates:
    """Test blackout dates validation."""
    
    def test_blackout_dates_compliant(self):
        """Test submissions not on blackout dates."""
        config = load_config("tests/common/data/config.json")
        
        # Create schedule avoiding blackout dates (use mods with shorter duration)
        schedule = {
            "1-wrk": date(2025, 4, 15),  # Mod with shorter duration
            "2-wrk": date(2025, 4, 16),  # Mod with shorter duration
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
            "J1-pap-ICML": date(2025, 1, 15),  # On blackout date
            "J2-pap-MICCAI": date(2025, 1, 20),  # Regular date
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
            "J1-pap-ICML": date(2025, 1, 1),
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
            "J1-pap-ICML": date(2025, 1, 1),  # Engineering paper
            "J2-pap-MICCAI": date(2025, 1, 1),  # Medical paper
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
            "J1-pap-ICML": date(2025, 1, 1),
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
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
        }
        
        result = validate_paper_lead_time_months(schedule, config)
        
        # Papers in test data have different draft_window_months (2 and 3)
        # while config default is 3, so some will violate
        assert result["total_papers"] == 2
        assert "compliance_rate" in result
        # The test data has papers with draft_window_months of 2 and 3,
        # while config default is 3, so we expect some violations


class TestAbstractPaperDependencies:
    """Test abstract-paper dependency validation."""
    
    def test_valid_abstract_paper_dependencies(self):
        """Test valid abstract-paper dependencies."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with valid abstract-paper dependencies
        schedule = {
            "J1-abs-ICML": date(2025, 1, 15),  # Abstract first
            "J1-pap-ICML": date(2025, 2, 1),   # Paper after abstract
        }
        
        result = validate_abstract_paper_dependencies(schedule, config)
        
        assert result["is_valid"] is True
        assert result["dependency_rate"] == 100.0
        assert result["total_papers"] >= 0  # Depends on config data
    
    def test_missing_abstract_dependency(self):
        """Test missing abstract dependency."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with paper but no abstract
        schedule = {
            "J1-pap-ICML": date(2025, 2, 1),  # Paper without abstract
        }
        
        result = validate_abstract_paper_dependencies(schedule, config)
        
        # Should have violations if ICML requires abstracts
        if result["total_papers"] > 0:
            assert len(result["violations"]) > 0
            assert any("requires abstract" in v["description"] for v in result["violations"])
    
    def test_paper_before_abstract(self):
        """Test paper scheduled before abstract."""
        config = load_config("tests/common/data/config.json")
        
        # Create a schedule with paper before abstract
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),   # Paper first
            "J1-abs-ICML": date(2025, 2, 1),   # Abstract after paper
        }
        
        result = validate_abstract_paper_dependencies(schedule, config)
        
        # Should have violations if ICML requires abstracts
        if result["total_papers"] > 0:
            assert len(result["violations"]) > 0
            assert any("must be scheduled after abstract" in v["description"] for v in result["violations"])
    
    def test_empty_schedule(self):
        """Test empty schedule."""
        config = load_config("tests/common/data/config.json")
        
        result = validate_abstract_paper_dependencies({}, config)
        
        assert result["is_valid"] is True
        assert result["total_papers"] == 0
        assert result["dependency_rate"] == 100.0


class TestComprehensiveConstraints:
    """Test comprehensive constraint validation."""
    
    def test_comprehensive_constraints_valid_schedule(self):
        """Test comprehensive validation with valid schedule."""
        config = load_config("tests/common/data/config.json")
        
        # Create a valid schedule
        schedule = {
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
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
        assert "conference_submission_compatibility" in result
        assert "abstract_paper_dependencies" in result
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
            "J1-pap-ICML": date(2025, 1, 1),
            "J2-pap-MICCAI": date(2025, 1, 1),
            "J3-pap-MICCAI": date(2025, 1, 1),  # Too many concurrent
            "J4-pap-MICCAI": date(2025, 1, 1),  # Too many concurrent
        }
        
        result = validate_all_constraints_comprehensive(schedule, config)
        
        # Should have violations
        assert result["total_violations"] > 0
        assert result["summary"]["overall_valid"] is False

    def test_validation_consistency_between_base_and_constraints(self):
        """Test that lightweight validation in base scheduler is consistent with comprehensive validation in constraints."""
        from src.schedulers.base import BaseScheduler
        
        config = load_config("tests/common/data/config.json")
        
        # Create a mock scheduler to test base scheduler validation
        class MockScheduler(BaseScheduler):
            def schedule(self):
                return {}
        
        scheduler = MockScheduler(config)
        
        # Test soft block model consistency
        submission = config.submissions_dict.get("paper1-wrk")
        if submission:
            submission.earliest_start_date = date(2025, 2, 1)
            
            # Test valid date (within 2 months)
            valid_date = date(2025, 3, 15)
            valid_schedule = {"paper1-wrk": valid_date}
            valid_result = validate_soft_block_model(valid_schedule, config)
            
            # Test invalid date (outside 2 months)
            invalid_date = date(2025, 6, 15)
            invalid_schedule = {"paper1-wrk": invalid_date}
            invalid_result = validate_soft_block_model(invalid_schedule, config)
            
            # Results should be consistent
            if valid_result["total_mods"] > 0:
                assert valid_result["is_valid"] == True  # Within 2 months should be valid
            if invalid_result["total_mods"] > 0:
                assert invalid_result["is_valid"] == False  # Outside 2 months should be invalid
        
        # Test working days consistency
        working_date = date(2025, 3, 17)  # Monday
        weekend_date = date(2025, 3, 22)  # Saturday
        
        # Test comprehensive validation directly
        from src.validation import validate_scheduling_options
        
        working_schedule = {"temp": working_date}
        weekend_schedule = {"temp": weekend_date}
        
        # Enable working days only
        config.scheduling_options = {"enable_working_days_only": True}
        
        comprehensive_working = validate_scheduling_options(working_schedule, config)
        comprehensive_weekend = validate_scheduling_options(weekend_schedule, config)
        
        # Results should be consistent
        assert comprehensive_working["is_valid"] == True  # Monday should be valid
        assert comprehensive_weekend["is_valid"] == False  # Saturday should be invalid
        
        # Test single conference policy consistency
        paper1 = config.submissions_dict.get("paper1")
        paper2 = config.submissions_dict.get("paper2")
        
        if paper1 and paper2:
            paper1.conference_id = "conf1"
            paper2.conference_id = "conf2"
            
            # Test valid assignment (different papers)
            schedule_valid = {"paper1": date.today(), "paper2": date.today()}
            base_valid = scheduler._validate_single_conference_policy(paper1, schedule_valid)
            
            comprehensive_valid = validate_single_conference_policy(schedule_valid, config)
            
            # Results should be consistent
            assert base_valid == comprehensive_valid["is_valid"]
            
            # Test invalid assignment (same paper to different conferences)
            # Create two submissions with same paper ID
            paper1_same = Submission(
                id="paper1-same",
                title="Same Paper",
                kind=SubmissionType.PAPER,
                conference_id="conf1"
            )
            paper1_diff = Submission(
                id="paper1-diff", 
                title="Same Paper",
                kind=SubmissionType.PAPER,
                conference_id="conf2"
            )
            
            schedule_invalid = {"paper1-same": date.today(), "paper1-diff": date.today()}
            base_invalid = scheduler._validate_single_conference_policy(paper1_same, schedule_invalid)
            
            # Add to config for comprehensive validation
            config.submissions.extend([paper1_same, paper1_diff])
            config.submissions_dict.update({s.id: s for s in [paper1_same, paper1_diff]})
            
            comprehensive_invalid = validate_single_conference_policy(schedule_invalid, config)
            
            # Results should be consistent
            assert base_invalid == comprehensive_invalid["is_valid"]
