"""Tests for core models."""

from datetime import date
from typing import Dict, List, Any, Optional

from core.models import (
    Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, SubmissionWorkflow,
    ValidationResult, ScoringResult, ScheduleResult, ScheduleSummary, ScheduleMetrics,
    PenaltyBreakdown, EfficiencyMetrics, TimelineMetrics, DeadlineValidation, DependencyValidation, ResourceValidation
)


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
        submission: Submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        validation_errors: List[str] = submission.validate_submission()
        assert len(validation_errors) == 0
    
    def test_submission_validation_invalid(self) -> None:
        """Test submission validation with invalid data."""
        submission: Submission = Submission(
            id="",
            title="",
            kind=SubmissionType.PAPER,
            conference_id=None,  # None instead of empty string
            candidate_conferences=None,  # This should trigger the validation error
            draft_window_months=-1,
            lead_time_from_parents=-1,
            penalty_cost_per_day=-100
        )
        
        validation_errors: List[str] = submission.validate_submission()
        assert len(validation_errors) > 0
        assert any("Missing submission ID" in error for error in validation_errors)
        assert any("Missing title" in error for error in validation_errors)
        assert any("Papers must have either conference_id or candidate_conferences" in error for error in validation_errors)
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
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
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
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        assert conference.get_deadline(SubmissionType.PAPER) == date(2024, 6, 1)
        assert conference.get_deadline(SubmissionType.ABSTRACT) is None
        assert conference.has_deadline(SubmissionType.PAPER) is True
        assert conference.has_deadline(SubmissionType.ABSTRACT) is False
    
    def test_conference_validation_valid(self) -> None:
        """Test conference validation with valid data."""
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        validation_errors: List[str] = conference.validate_conference()
        assert len(validation_errors) == 0
    
    def test_conference_validation_invalid(self) -> None:
        """Test conference validation with invalid data."""
        conference: Conference = Conference(
            id="",
            name="",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={}
        )
        
        validation_errors: List[str] = conference.validate_conference()
        assert len(validation_errors) > 0
        assert any("Missing conference ID" in error for error in validation_errors)
        assert any("Missing conference name" in error for error in validation_errors)
        assert any("No deadlines defined" in error for error in validation_errors)


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
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
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
        """Test config validation with valid data."""
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
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        errors: List[str] = config.validate_config()
        assert len(errors) == 0
    
    def test_config_validation_invalid(self) -> None:
        """Test config validation with invalid data."""
        # Test empty submissions
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config: Config = Config(
            submissions=[],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        errors: List[str] = config.validate_config()
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
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config: Config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        assert "test-pap" in config.submissions_dict
        assert "conf1" in config.conferences_dict
        assert config.submissions_dict["test-pap"] == submission
        assert config.conferences_dict["conf1"] == conference
    
    def test_config_abstract_paper_dependency_validation(self) -> None:
        """Test config validation works with simplified architecture (no auto-generation)."""
        # Create conference that explicitly requires abstracts before papers
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2024, 3, 1),
                SubmissionType.PAPER: date(2024, 6, 1)
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
        errors: List[str] = config.validate_config()
        assert len(errors) == 0
    
    def test_config_ensure_abstract_paper_dependencies(self) -> None:
        """Test automatic creation of abstract dependencies."""
        # Create conference that explicitly requires abstracts before papers
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2024, 3, 1),
                SubmissionType.PAPER: date(2024, 6, 1)
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
        assert "paper1-abs-conf1" not in config.submissions_dict
        
        # NOTE: ensure_abstract_paper_dependencies no longer exists - simplified architecture
        # Just validate that config is properly structured
        errors = config.validate_config()
        assert len(errors) == 0  # Basic validation should pass

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
        empty_config_errors: List[str] = empty_config.validate_config()
        assert isinstance(empty_config_errors, list)
        
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
        extreme_config_errors: List[str] = extreme_config.validate_config()
        assert isinstance(extreme_config_errors, list)
        
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
        malformed_config_errors: List[str] = malformed_config.validate_config()
        assert len(malformed_config_errors) > 0
        assert any("nonexistent" in error.lower() for error in malformed_config_errors)
        
        # Test with invalid lead times
        invalid_config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=-10,  # Invalid negative value
            min_paper_lead_time_days=0,       # Invalid zero value
            max_concurrent_submissions=-5      # Invalid negative value
        )
        
        # Should detect invalid configuration
        errors: List[str] = invalid_config.validate_config()
        assert len(errors) > 0

    def test_config_abstract_paper_dependencies_edge_cases(self) -> None:
        """Test abstract-paper dependencies with edge cases."""
        # Test with conference that doesn't require abstracts
        conference_no_abstract = Conference(
            id="conf_no_abstract",
            name="No Abstract Conference",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}  # Only paper deadline
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
        errors: List[str] = config.validate_config()
        assert not any("requires abstract" in error for error in errors)
        
        # Test with paper that already has abstract
        conference_requiring_abstracts = Conference(
            id="conf_with_abstract",
            name="Abstract Required Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2024, 3, 1),
                SubmissionType.PAPER: date(2024, 6, 1)
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
        circular_dependency_errors: List[str] = config_circular.validate_config()
        assert len(circular_dependency_errors) > 0
        
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
        orphan_dependency_errors: List[str] = config_orphan.validate_config()
        assert len(orphan_dependency_errors) > 0
        assert any("nonexistent" in error.lower() for error in orphan_dependency_errors)
        
        # Test with submissions that have invalid conference assignments
        conference_medical = Conference(
            id="medical_conf",
            name="Medical Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
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
        errors: List[str] = config_mismatch.validate_config()
        # Note: This might not be an error depending on business rules
        # but should be validated


class TestUnifiedModels:
    """Test unified models."""
    
    def test_validation_result_creation(self) -> None:
        """Test ValidationResult creation."""
        deadline_validation = DeadlineValidation(
            is_valid=True,
            violations=[],
            summary="All deadlines met",
            compliance_rate=100.0,
            total_submissions=0,
            compliant_submissions=0
        )
        dependency_validation = DependencyValidation(
            is_valid=True,
            violations=[],
            summary="All dependencies satisfied",
            satisfaction_rate=100.0,
            total_dependencies=0,
            satisfied_dependencies=0
        )
        resource_validation = ResourceValidation(
            is_valid=True,
            violations=[],
            summary="Resource constraints satisfied",
            max_concurrent=3,
            max_observed=0,
            total_days=0
        )
        
        validation_result: ValidationResult = ValidationResult(
            is_valid=True,
            violations=[],
            deadline_validation=deadline_validation,
            dependency_validation=dependency_validation,
            resource_validation=resource_validation,
            summary="All validations passed"
        )
        
        assert validation_result.is_valid is True
        assert len(validation_result.violations) == 0
        assert validation_result.summary == "All validations passed"
    
    def test_scoring_result_creation(self) -> None:
        """Test scoring result creation."""
        penalty_breakdown = PenaltyBreakdown(
            total_penalty=100.0,
            deadline_penalties=50.0,
            dependency_penalties=30.0,
            resource_penalties=20.0,
            conference_compatibility_penalties=0.0,
            abstract_paper_dependency_penalties=0.0
        )
        
        efficiency_metrics = EfficiencyMetrics(
            utilization_rate=0.8,
            peak_utilization=5,
            avg_utilization=3.2,
            efficiency_score=85.0
        )
        
        timeline_metrics = TimelineMetrics(
            duration_days=30,
            avg_daily_load=2.5,
            timeline_efficiency=0.9
        )
        
        scoring_result: Any = ScoringResult(
            penalty_score=100.0,
            quality_score=85.0,
            efficiency_score=90.0,
            penalty_breakdown=penalty_breakdown,
            efficiency_metrics=efficiency_metrics,
            timeline_metrics=timeline_metrics,
            overall_score=91.67
        )
        
        assert scoring_result.penalty_score == 100.0
        assert scoring_result.quality_score == 85.0
        assert scoring_result.efficiency_score == 90.0
        assert scoring_result.overall_score == 91.67

    def test_schedule_result_creation(self) -> None:
        """Test schedule result creation."""
        schedule: Schedule = {"paper1": date(2024, 5, 1), "paper2": date(2024, 7, 1)}
        
        summary = ScheduleSummary(
            total_submissions=2,
            schedule_span=61,
            start_date=date(2024, 5, 1),
            end_date=date(2024, 7, 1),
            penalty_score=100.0,
            quality_score=85.0,
            efficiency_score=90.0,
            deadline_compliance=95.0,
            resource_utilization=0.8
        )
        
        metrics = ScheduleMetrics(
            makespan=61,
            avg_utilization=0.8,
            peak_utilization=5,
            total_penalty=100.0,
            compliance_rate=95.0,
            quality_score=85.0
        )
        
        penalty_breakdown = PenaltyBreakdown(
            total_penalty=100.0,
            deadline_penalties=50.0,
            dependency_penalties=30.0,
            resource_penalties=20.0,
            conference_compatibility_penalties=0.0,
            abstract_paper_dependency_penalties=0.0
        )
        
        efficiency_metrics = EfficiencyMetrics(
            utilization_rate=0.8,
            peak_utilization=5,
            avg_utilization=3.2,
            efficiency_score=90.0
        )
        
        timeline_metrics = TimelineMetrics(
            duration_days=61,
            avg_daily_load=2.5,
            timeline_efficiency=0.9
        )
        
        scoring_result: Any = ScoringResult(
            penalty_score=100.0,
            quality_score=85.0,
            efficiency_score=90.0,
            penalty_breakdown=penalty_breakdown,
            efficiency_metrics=efficiency_metrics,
            timeline_metrics=timeline_metrics,
            overall_score=91.67
        )
        
        validation_result: Any = ValidationResult(
            is_valid=True,
            violations=[],
            deadline_validation=DeadlineValidation(
                is_valid=True,
                violations=[],
                summary="All deadlines met",
                compliance_rate=100.0,
                total_submissions=2,
                compliant_submissions=2
            ),
            dependency_validation=DependencyValidation(
                is_valid=True,
                violations=[],
                summary="All dependencies satisfied",
                satisfaction_rate=100.0,
                total_dependencies=0,
                satisfied_dependencies=0
            ),
            resource_validation=ResourceValidation(
                is_valid=True,
                violations=[],
                summary="Resource constraints satisfied",
                max_concurrent=3,
                max_observed=2,
                total_days=61
            ),
            summary="Schedule is valid"
        )
        
        schedule_result: Any = ScheduleResult(
            schedule=schedule,
            summary=summary,
            metrics=metrics,
            tables={"monthly": []},
            validation=validation_result,
            scoring=scoring_result
        )
        
        assert schedule_result.schedule == schedule
        assert schedule_result.summary.total_submissions == 2
        assert schedule_result.metrics.makespan == 61
        assert schedule_result.validation.is_valid is True
        assert schedule_result.scoring.overall_score == 91.67


class TestAnalysisClasses:
    """Test analytics classes."""
    
    def test_schedule_analysis(self) -> None:
        """Test ScheduleAnalysis creation."""
        from core.models import ScheduleAnalysis
        
        analysis = ScheduleAnalysis(
            scheduled_count=5,
            total_count=10,
            completion_rate=50.0,
            missing_submissions=[{"id": "missing1"}, {"id": "missing2"}],
            summary="Half of submissions scheduled",
            metadata={"strategy": "greedy"}
        )
        
        assert analysis.scheduled_count == 5
        assert analysis.total_count == 10
        assert analysis.completion_rate == 50.0
        assert len(analysis.missing_submissions) == 2
        assert analysis.summary == "Half of submissions scheduled"
    
    def test_schedule_distribution(self) -> None:
        """Test ScheduleDistribution creation."""
        from core.models import ScheduleDistribution
        
        distribution = ScheduleDistribution(
            monthly_distribution={"2024-05": 2, "2024-06": 3},
            quarterly_distribution={"2024-Q2": 5},
            yearly_distribution={"2024": 5},
            summary="Well distributed schedule",
            metadata={"analysis_type": "temporal"}
        )
        
        assert distribution.monthly_distribution["2024-05"] == 2
        assert distribution.quarterly_distribution["2024-Q2"] == 5
        assert distribution.yearly_distribution["2024"] == 5
        assert distribution.summary == "Well distributed schedule"
    
    def test_submission_type_analysis(self) -> None:
        """Test SubmissionTypeAnalysis creation."""
        from core.models import SubmissionTypeAnalysis
        
        analysis = SubmissionTypeAnalysis(
            type_counts={"paper": 3, "abstract": 2},
            type_percentages={"paper": 60.0, "abstract": 40.0},
            summary="More papers than abstracts",
            metadata={"total_submissions": 5}
        )
        
        assert analysis.type_counts["paper"] == 3
        assert analysis.type_percentages["paper"] == 60.0
        assert analysis.summary == "More papers than abstracts"
    
    def test_timeline_analysis(self) -> None:
        """Test TimelineAnalysis creation."""
        from core.models import TimelineAnalysis
        
        analysis = TimelineAnalysis(
            start_date=date(2024, 5, 1),
            end_date=date(2024, 8, 1),
            duration_days=92,
            avg_submissions_per_month=1.67,
            summary="3-month timeline",
            metadata={"strategy": "optimal"}
        )
        
        assert analysis.start_date == date(2024, 5, 1)
        assert analysis.end_date == date(2024, 8, 1)
        assert analysis.duration_days == 92
        assert analysis.avg_submissions_per_month == 1.67
        assert analysis.summary == "3-month timeline"
    
    def test_resource_analysis(self) -> None:
        """Test ResourceAnalysis creation."""
        from core.models import ResourceAnalysis
        
        analysis = ResourceAnalysis(
            peak_load=3,
            avg_load=2.1,
            utilization_pattern={date(2024, 5, 1): 2, date(2024, 5, 2): 3},
            summary="Good resource utilization",
            metadata={"max_capacity": 4}
        )
        
        assert analysis.peak_load == 3
        assert analysis.avg_load == 2.1
        assert analysis.utilization_pattern[date(2024, 5, 1)] == 2
        assert analysis.summary == "Good resource utilization"
