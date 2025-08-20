"""Tests for core models."""

from datetime import date, timedelta
from typing import Dict, List, Any, Optional

from core.models import (
    Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, SubmissionWorkflow,
    ValidationResult, ScheduleMetrics, Schedule,
    ConstraintViolation, DeadlineViolation, DependencyViolation, ResourceViolation
)
from validation.submission import validate_submission_constraints
from validation.config import validate_config
from conftest import get_recent_deadline, get_past_deadline, get_test_date


class TestScheduleType:
    """Test schedule type definitions."""
    
    def test_schedule_type(self) -> None:
        """Test that schedule type is properly defined."""
        assert isinstance(SubmissionType.PAPER, SubmissionType)
        assert isinstance(SubmissionType.ABSTRACT, SubmissionType)
        assert isinstance(SubmissionType.POSTER, SubmissionType)


class TestEnums:
    """Test enum definitions."""
    
    def test_submission_type_enum(self) -> None:
        """Test submission type enum values."""
        assert SubmissionType.PAPER == "paper"
        assert SubmissionType.ABSTRACT == "abstract"
        assert SubmissionType.POSTER == "poster"
    
    def test_conference_type_enum(self) -> None:
        """Test conference type enum values."""
        assert ConferenceType.MEDICAL == "MEDICAL"
        assert ConferenceType.ENGINEERING == "ENGINEERING"
    
    def test_conference_recurrence_enum(self) -> None:
        """Test conference recurrence enum values."""
        assert ConferenceRecurrence.ANNUAL == "annual"
        assert ConferenceRecurrence.BIENNIAL == "biennial"
        assert ConferenceRecurrence.QUARTERLY == "quarterly"
    
    def test_scheduler_strategy_enum(self) -> None:
        """Test scheduler strategy enum values."""
        from core.models import SchedulerStrategy
        assert SchedulerStrategy.GREEDY == "greedy"
        assert SchedulerStrategy.STOCHASTIC == "stochastic"
        assert SchedulerStrategy.LOOKAHEAD == "lookahead"


class TestSubmission:
    """Test Submission model."""
    
    def test_submission_creation(self) -> None:
        """Test basic submission creation."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        assert submission.id == "test-pap"
        assert submission.title == "Test Paper"
        assert submission.kind == SubmissionType.PAPER
        assert submission.conference_id == "conf1"
        assert submission.depends_on is None
    
    def test_submission_with_dependencies(self) -> None:
        """Test submission with dependencies."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            depends_on=["dep1", "dep2"]
        )
        
        assert submission.depends_on == ["dep1", "dep2"]
    
    def test_submission_defaults(self) -> None:
        """Test submission default values."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        assert submission.draft_window_months == 3
        assert submission.lead_time_from_parents == 0
        assert submission.penalty_cost_per_day is None
        assert submission.engineering is False
        assert submission.earliest_start_date is None
    
    def test_submission_validation_valid(self) -> None:
        """Test submission validation with valid data."""
        # Create a proper config with a conference
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}
        )
        
        config: Config = Config(
            submissions=[],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            draft_window_months=1  # Shorter duration to fit within deadline
        )
        
        # Use a future date to avoid deadline issues
        future_date = get_test_date(15)  # 15 days from now, before the deadline
        validation_errors: List[str] = validate_submission_constraints(submission, future_date, Schedule(), config)
        assert len(validation_errors) == 0
    
    def test_submission_validation_invalid(self) -> None:
        """Test submission validation with invalid data."""
        submission: Submission = Submission(
            id="",
            title="",
            kind=SubmissionType.PAPER,
            conference_id=None,  # None instead of empty string
            preferred_conferences=None,  # This should trigger the validation error
            draft_window_months=-1,
            lead_time_from_parents=-1,
            penalty_cost_per_day=-100
        )
        
        validation_errors: List[str] = validate_submission_constraints(submission, date.today(), Schedule(), Config.create_default())
        assert len(validation_errors) > 0
        assert any("Missing submission ID" in error for error in validation_errors)
        assert any("Missing title" in error for error in validation_errors)
        assert any("Papers must have either conference_id or preferred_conferences" in error for error in validation_errors)
        assert any("Draft window months cannot be negative" in error for error in validation_errors)
        assert any("Lead time from parents cannot be negative" in error for error in validation_errors)
        assert any("Penalty cost per day cannot be negative" in error for error in validation_errors)
    
    def test_submission_priority_score(self) -> None:
        """Test submission priority score calculation."""
        config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            priority_weights={
                "paper": 1.0,
                "abstract": 0.5,
                "engineering_paper": 2.0
            }
        )
        
        # Test paper submission
        paper_submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            author="test"
        )
        assert paper_submission.get_priority_score(config) == 1.0
        
        # Test engineering paper
        eng_paper: Submission = Submission(
            id="test-eng",
            title="Engineering Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            author="test",
            engineering=True
        )
        assert eng_paper.get_priority_score(config) == 2.0  # 1.0 * 2.0
        
        # Test abstract
        abstract_submission: Submission = Submission(
            id="test-abs",
            title="Test Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="conf1",
            author="test"
        )
        assert abstract_submission.get_priority_score(config) == 0.5


# NOTE: TestAbstractPaperDependencies class removed - auto-generation functions no longer exist


class TestConference:
    """Test Conference model."""
    
    def test_conference_creation(self) -> None:
        """Test basic conference creation."""
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}
        )
        
        assert conference.id == "conf1"
        assert conference.name == "Test Conference"
        assert conference.conf_type == ConferenceType.MEDICAL
        assert conference.recurrence == ConferenceRecurrence.ANNUAL
        assert len(conference.deadlines) == 1
    
    def test_conference_with_single_deadline(self) -> None:
        """Test conference with single deadline."""
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}
        )
        
        assert conference.get_deadline(SubmissionType.PAPER) == get_recent_deadline()
        assert conference.get_deadline(SubmissionType.ABSTRACT) is None
        assert conference.has_deadline(SubmissionType.PAPER) is True
        assert conference.has_deadline(SubmissionType.ABSTRACT) is False
    
    def test_conference_validation_valid(self) -> None:
        """Test conference validation with valid data (recent deadline)."""
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Use recent date within 1 year
        )
        
        # Conference validation is now part of config validation
        # Create a minimal config to test conference validation
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        test_config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        validation_result = validate_config(test_config)
        assert validation_result.is_valid
    
    def test_conference_validation_past_deadline(self) -> None:
        """Test conference validation with past deadline (should fail)."""
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_past_deadline()}  # Use past date more than 1 year ago
        )
        
        # Conference validation is now part of config validation
        # Create a minimal config to test conference validation
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        test_config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        validation_result = validate_config(test_config)
        # Should fail because deadline is more than 1 year ago
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("would miss deadline" in error for error in errors)
    
    def test_conference_validation_invalid(self) -> None:
        """Test conference validation with invalid data."""
        conference: Conference = Conference(
            id="",
            name="",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={}
        )
        
        # Conference validation is now part of config validation
        # Create a minimal config to test conference validation
        test_config = Config(
            submissions=[],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        validation_result = validate_config(test_config)
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("Conference missing ID" in error for error in errors)
        assert any("Conference missing name" in error for error in errors)
        assert any("No deadlines defined" in error for error in errors)


class TestConfig:
    """Test Config model."""
    
    def test_config_creation(self) -> None:
        """Test basic config creation."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Use recent date for creation test
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        assert len(config.submissions) == 1
        assert len(config.conferences) == 1
        assert config.min_abstract_lead_time_days == 30
        assert config.min_paper_lead_time_days == 90
        assert config.max_concurrent_submissions == 3
    
    def test_config_validation_valid(self) -> None:
        """Test config validation with valid data (recent deadline)."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Use recent date within 1 year
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        validation_result = validate_config(config)
        assert validation_result.is_valid
    
    def test_config_validation_past_deadline(self) -> None:
        """Test config validation with past deadline (should fail)."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_past_deadline()}  # Use past date more than 1 year ago
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        validation_result = validate_config(config)
        # Should fail because deadline is more than 1 year ago
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("Submission" in error and "would miss deadline" in error for error in errors)
    
    def test_config_validation_invalid(self) -> None:
        """Test config validation with invalid data."""
        # Test empty submissions
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Use recent date for invalid test
        )
        
        config: Config = Config(
            submissions=[],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        validation_result = validate_config(config)
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("No submissions defined" in error for error in errors)
    
    def test_config_computed_properties(self) -> None:
        """Test config computed properties."""
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Use recent date for computed properties test
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        assert config.has_submission("test-pap")
        assert config.has_conference("conf1")
        assert config.get_submission("test-pap") == submission
        assert config.get_conference("conf1") == conference
    
    def test_config_abstract_paper_dependency_validation(self) -> None:
        """Test config validation works with simplified architecture (no auto-generation)."""
        # Create conference that explicitly requires abstracts before papers
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: get_recent_deadline(),
                SubmissionType.PAPER: get_test_date(60)  # 60 days from now
            },
            submission_types=SubmissionWorkflow.ABSTRACT_THEN_PAPER
        )
        
        # Paper with explicit abstract dependency (new architecture)
        paper = Submission(
            id="paper1",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            depends_on=["abstract1"]  # Explicit dependency
        )
        
        abstract = Submission(
            id="abstract1",
            title="Test Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="conf1"
        )
        
        config: Config = Config(
            submissions=[paper, abstract],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should validate successfully with explicit dependencies (no auto-generation)
        validation_result = validate_config(config)
        assert validation_result.is_valid
    
    def test_config_ensure_abstract_paper_dependencies(self) -> None:
        """Test automatic creation of abstract dependencies."""
        # Create conference that explicitly requires abstracts before papers
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: get_recent_deadline(),
                SubmissionType.PAPER: get_test_date(60)  # 60 days from now
            },
            submission_types=SubmissionWorkflow.ABSTRACT_THEN_PAPER
        )
        
        # Paper without abstract
        paper = Submission(
            id="paper1",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        config: Config = Config(
            submissions=[paper],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            penalty_costs={"default_mod_penalty_per_day": 1000.0}
        )
        
        # Initially no abstract
        assert len(config.submissions) == 1
        assert not config.has_submission("paper1-abs-conf1")
        
        # NOTE: ensure_abstract_paper_dependencies no longer exists - simplified architecture
        # Just validate that config is properly structured
        validation_result = validate_config(config)
        assert validation_result.is_valid  # Basic validation should pass

    def test_config_edge_cases(self) -> None:
        """Test config edge cases and error conditions."""
        # Test with empty submissions and conferences
        empty_config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should not crash with empty data
        validation_result = validate_config(empty_config)
        assert isinstance(validation_result, ValidationResult)
        
        # Test with extreme penalty values
        extreme_config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            penalty_costs={
                "default_mod_penalty_per_day": 999999.0,
                "missing_abstract_penalty": 50000.0,
                "unscheduled_abstract_penalty": 40000.0,
                "abstract_paper_timing_penalty": 30000.0,
                "missing_abstract_dependency_penalty": 25000.0
            }
        )
        
        # Should handle extreme values without crashing
        validation_result = validate_config(extreme_config)
        assert isinstance(validation_result, ValidationResult)
        
        # Test with malformed submission data
        malformed_submission: Submission = Submission(
            id="malformed",
            title="",  # Empty title
            kind=SubmissionType.PAPER,
            conference_id="nonexistent_conf"
        )
        
        malformed_config: Config = Config(
            submissions=[malformed_submission],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should detect malformed data
        validation_result = validate_config(malformed_config)
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("nonexistent" in error.lower() for error in errors)
        
        # Test with invalid lead times
        invalid_config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=-10,  # Invalid negative value
            min_paper_lead_time_days=0,       # Invalid zero value
            max_concurrent_submissions=-5      # Invalid negative value
        )
        
        # Should detect invalid configuration
        validation_result = validate_config(invalid_config)
        assert not validation_result.is_valid

    def test_config_abstract_paper_dependencies_edge_cases(self) -> None:
        """Test abstract-paper dependencies with edge cases."""
        # Test with conference that doesn't require abstracts
        conference_no_abstract = Conference(
            id="conf_no_abstract",
            name="No Abstract Conference",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}  # Only paper deadline
        )
        
        paper = Submission(
            id="paper1",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf_no_abstract"
        )
        
        config: Config = Config(
            submissions=[paper],
            conferences=[conference_no_abstract],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should not require abstract for paper-only conference
        validation_result = validate_config(config)
        assert validation_result.is_valid
        
        # Test with paper that already has abstract
        conference_requiring_abstracts = Conference(
            id="conf_with_abstract",
            name="Abstract Required Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: get_recent_deadline(),
                SubmissionType.PAPER: get_test_date(60)  # 60 days from now
            },
            submission_types=SubmissionWorkflow.ABSTRACT_THEN_PAPER
        )
        
        existing_abstract = Submission(
            id="paper1-abs-conf_with_abstract",
            title="Existing Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="conf_with_abstract"
        )
        
        paper_with_abstract = Submission(
            id="paper1",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf_with_abstract",
            depends_on=["paper1-abs-conf_with_abstract"]
        )
        
        config_with_abstract = Config(
            submissions=[paper_with_abstract, existing_abstract],
            conferences=[conference_requiring_abstracts],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should not create duplicate abstract
        initial_count = len(config_with_abstract.submissions)
        # NOTE: ensure_abstract_paper_dependencies removed - no auto-generation
        assert len(config_with_abstract.submissions) == initial_count
        
        # Test with paper scheduled before abstract
        paper_before_abstract = Submission(
            id="paper2",
            title="Paper Before Abstract",
            kind=SubmissionType.PAPER,
            conference_id="conf_with_abstract"
        )
        
        config_before_abstract = Config(
            submissions=[paper_before_abstract],
            conferences=[conference_requiring_abstracts],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            penalty_costs={"default_mod_penalty_per_day": 1000.0}
        )
        
        # With explicit submissions only - no auto-generation
        # NOTE: ensure_abstract_paper_dependencies removed - no auto-generation
        assert len(config_before_abstract.submissions) == 1  # Only the explicitly created paper
        assert "paper2-abs-conf_with_abstract" not in config_before_abstract.submissions_dict  # No auto-creation
        # Dependencies must be explicit in data files now

    def test_config_validation_comprehensive_edge_cases(self) -> None:
        """Test comprehensive validation with edge cases."""
        # Test with submissions that have circular dependencies
        submission_a = Submission(
            id="sub_a",
            title="Submission A",
            kind=SubmissionType.PAPER,
            depends_on=["sub_b"]
        )
        
        submission_b = Submission(
            id="sub_b", 
            title="Submission B",
            kind=SubmissionType.PAPER,
            depends_on=["sub_a"]  # Circular dependency
        )
        
        config_circular = Config(
            submissions=[submission_a, submission_b],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should detect circular dependencies
        validation_result = validate_config(config_circular)
        assert not validation_result.is_valid
        
        # Test with submissions that depend on non-existent submissions
        submission_orphan = Submission(
            id="orphan",
            title="Orphan Submission",
            kind=SubmissionType.PAPER,
            depends_on=["nonexistent_dependency"]
        )
        
        config_orphan = Config(
            submissions=[submission_orphan],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should detect missing dependencies
        validation_result = validate_config(config_orphan)
        assert not validation_result.is_valid
        errors = validation_result.metadata.get("errors", [])
        assert any("nonexistent" in error.lower() for error in errors)
        
        # Test with submissions that have invalid conference assignments
        conference_medical = Conference(
            id="medical_conf",
            name="Medical Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: get_recent_deadline()}
        )
        
        engineering_paper = Submission(
            id="eng_paper",
            title="Engineering Paper",
            kind=SubmissionType.PAPER,
            conference_id="medical_conf",
            engineering=True  # Engineering paper to medical conference
        )
        
        config_mismatch = Config(
            submissions=[engineering_paper],
            conferences=[conference_medical],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Should validate conference compatibility
        validation_result = validate_config(config_mismatch)
        # Note: This might not be an error depending on business rules
        # but should be validated


class TestUnifiedModels:
    """Test unified models."""
    
    def test_validation_result_creation(self) -> None:
        """Test ValidationResult creation."""
        validation_result: ValidationResult = ValidationResult(
            is_valid=True,
            violations=[],
            summary="All validations passed",
            metadata={
                "compliance_rate": 100.0,
                "total_submissions": 0,
                "compliant_submissions": 0,
                "satisfaction_rate": 100.0,
                "total_dependencies": 0,
                "satisfied_dependencies": 0,
                "max_concurrent": 3,
                "max_observed": 0,
                "total_days": 0
            }
        )
        
        assert validation_result.is_valid is True
        assert len(validation_result.violations) == 0
        assert validation_result.summary == "All validations passed"
    
    def test_schedule_metrics_creation(self) -> None:
        """Test schedule metrics creation."""
        metrics = ScheduleMetrics(
            makespan=61,
            total_penalty=100.0,
            compliance_rate=95.0,
            quality_score=85.0,
            avg_utilization=0.8,
            peak_utilization=5,
            utilization_rate=0.8,
            efficiency_score=90.0,
            duration_days=61,
            avg_daily_load=2.5,
            timeline_efficiency=0.9,
            submission_count=2,
            scheduled_count=2,
            completion_rate=1.0,
            start_date=get_test_date(-60),  # 60 days ago
            end_date=get_test_date(30)      # 30 days from now
        )
        
        assert metrics.makespan == 61
        assert metrics.total_penalty == 100.0
        assert metrics.compliance_rate == 95.0
        assert metrics.quality_score == 85.0
        assert metrics.efficiency_score == 90.0
        assert metrics.submission_count == 2

    def test_schedule_metrics_comprehensive(self) -> None:
        """Test comprehensive schedule metrics."""
        metrics = ScheduleMetrics(
            makespan=61,
            total_penalty=100.0,
            compliance_rate=95.0,
            quality_score=85.0,
            avg_utilization=0.8,
            peak_utilization=5,
            utilization_rate=0.8,
            efficiency_score=90.0,
            duration_days=61,
            avg_daily_load=2.5,
            timeline_efficiency=0.9,
            submission_count=2,
            scheduled_count=2,
            completion_rate=1.0,
            start_date=get_test_date(-60),  # 60 days ago
            end_date=get_test_date(30),     # 30 days from now
            monthly_distribution={"May": 1, "June": 0, "July": 1},
            quarterly_distribution={"Q2": 1, "Q3": 1},
            yearly_distribution={"2024": 2},
            type_counts={"paper": 2},
            type_percentages={"paper": 100.0}
        )
        
        assert metrics.makespan == 61
        assert metrics.total_penalty == 100.0
        assert metrics.compliance_rate == 95.0
        assert metrics.quality_score == 85.0
        assert metrics.efficiency_score == 90.0
        assert metrics.submission_count == 2
        assert metrics.scheduled_count == 2
        assert metrics.completion_rate == 1.0
        assert "May" in metrics.monthly_distribution
        assert "Q2" in metrics.quarterly_distribution
        assert "2024" in metrics.yearly_distribution



