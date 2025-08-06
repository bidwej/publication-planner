"""Tests for core models."""

import pytest
from datetime import date
from src.core.models import (
    Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence,
    Config, ValidationResult, ScoringResult, ScheduleResult, ScheduleSummary, ScheduleMetrics,
    PenaltyBreakdown, EfficiencyMetrics, TimelineMetrics
)


class TestScheduleType:
    """Test schedule type definitions."""
    
    def test_schedule_type(self):
        """Test that schedule type is properly defined."""
        assert isinstance(SubmissionType.PAPER, SubmissionType)
        assert isinstance(SubmissionType.ABSTRACT, SubmissionType)
        assert isinstance(SubmissionType.POSTER, SubmissionType)


class TestEnums:
    """Test enum definitions."""
    
    def test_submission_type_enum(self):
        """Test submission type enum values."""
        assert SubmissionType.PAPER == "paper"
        assert SubmissionType.ABSTRACT == "abstract"
        assert SubmissionType.POSTER == "poster"
    
    def test_conference_type_enum(self):
        """Test conference type enum values."""
        assert ConferenceType.MEDICAL == "MEDICAL"
        assert ConferenceType.ENGINEERING == "ENGINEERING"
    
    def test_conference_recurrence_enum(self):
        """Test conference recurrence enum values."""
        assert ConferenceRecurrence.ANNUAL == "annual"
        assert ConferenceRecurrence.BIENNIAL == "biennial"
        assert ConferenceRecurrence.QUARTERLY == "quarterly"
    
    def test_scheduler_strategy_enum(self):
        """Test scheduler strategy enum values."""
        from src.core.models import SchedulerStrategy
        assert SchedulerStrategy.GREEDY == "greedy"
        assert SchedulerStrategy.STOCHASTIC == "stochastic"
        assert SchedulerStrategy.LOOKAHEAD == "lookahead"


class TestSubmission:
    """Test Submission model."""
    
    def test_submission_creation(self):
        """Test basic submission creation."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        assert submission.id == "test-pap"
        assert submission.title == "Test Paper"
        assert submission.kind == SubmissionType.PAPER
        assert submission.conference_id == "conf1"
        assert submission.depends_on == []
    
    def test_submission_with_dependencies(self):
        """Test submission with dependencies."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            depends_on=["dep1", "dep2"]
        )
        
        assert submission.depends_on == ["dep1", "dep2"]
    
    def test_submission_defaults(self):
        """Test submission default values."""
        submission = Submission(
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
    
    def test_submission_validation_valid(self):
        """Test submission validation with valid data."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        errors = submission.validate()
        assert len(errors) == 0
    
    def test_submission_validation_invalid(self):
        """Test submission validation with invalid data."""
        submission = Submission(
            id="",
            title="",
            kind=SubmissionType.PAPER,
            conference_id="",
            draft_window_months=-1,
            lead_time_from_parents=-1,
            penalty_cost_per_day=-100
        )
        
        errors = submission.validate()
        assert len(errors) > 0
        assert any("Missing submission ID" in error for error in errors)
        assert any("Missing title" in error for error in errors)
        assert any("Missing conference ID" in error for error in errors)
        assert any("Draft window months cannot be negative" in error for error in errors)
        assert any("Lead time from parents cannot be negative" in error for error in errors)
        assert any("Penalty cost per day cannot be negative" in error for error in errors)
    
    def test_submission_priority_score(self):
        """Test submission priority score calculation."""
        config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            priority_weights={
                "paper_paper": 2.0,
                "abstract": 0.5,
                "engineering_paper": 1.5
            }
        )
        
        # Test paper submission
        paper_submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        assert paper_submission.get_priority_score(config) == 2.0
        
        # Test engineering paper
        eng_paper = Submission(
            id="test-eng",
            title="Engineering Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1",
            engineering=True
        )
        assert eng_paper.get_priority_score(config) == 3.0  # 2.0 * 1.5
        
        # Test abstract
        abstract_submission = Submission(
            id="test-abs",
            title="Test Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="conf1"
        )
        assert abstract_submission.get_priority_score(config) == 0.5


class TestConference:
    """Test Conference model."""
    
    def test_conference_creation(self):
        """Test basic conference creation."""
        conference = Conference(
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
    
    def test_conference_with_single_deadline(self):
        """Test conference with single deadline."""
        conference = Conference(
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
    
    def test_conference_validation_valid(self):
        """Test conference validation with valid data."""
        conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        errors = conference.validate()
        assert len(errors) == 0
    
    def test_conference_validation_invalid(self):
        """Test conference validation with invalid data."""
        conference = Conference(
            id="",
            name="",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={}
        )
        
        errors = conference.validate()
        assert len(errors) > 0
        assert any("Missing conference ID" in error for error in errors)
        assert any("Missing conference name" in error for error in errors)
        assert any("No deadlines defined" in error for error in errors)


class TestConfig:
    """Test Config model."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = Config(
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
    
    def test_config_validation_valid(self):
        """Test config validation with valid data."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = Config(
            submissions=[submission],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        errors = config.validate()
        assert len(errors) == 0
    
    def test_config_validation_invalid(self):
        """Test config validation with invalid data."""
        # Test empty submissions
        conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = Config(
            submissions=[],
            conferences=[conference],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        errors = config.validate()
        assert any("No submissions defined" in error for error in errors)
    
    def test_config_computed_properties(self):
        """Test config computed properties."""
        submission = Submission(
            id="test-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date(2024, 6, 1)}
        )
        
        config = Config(
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


class TestUnifiedModels:
    """Test unified models."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        validation_result = ValidationResult(
            is_valid=True,
            violations=[],
            deadline_validation={},
            dependency_validation={},
            resource_validation={},
            summary="All validations passed"
        )
        
        assert validation_result.is_valid is True
        assert len(validation_result.violations) == 0
        assert validation_result.summary == "All validations passed"
    
    def test_scoring_result_creation(self):
        """Test ScoringResult creation."""
        penalty_breakdown = PenaltyBreakdown(
            total_penalty=10.0,
            deadline_penalties=5.0,
            dependency_penalties=3.0,
            resource_penalties=2.0
        )
        
        efficiency_metrics = EfficiencyMetrics(
            utilization_rate=80.0,
            peak_utilization=3,
            avg_utilization=2.5,
            efficiency_score=85.0
        )
        
        timeline_metrics = TimelineMetrics(
            duration_days=90,
            avg_daily_load=1.5,
            timeline_efficiency=90.0
        )
        
        scoring_result = ScoringResult(
            penalty_score=10.0,
            quality_score=85.0,
            efficiency_score=85.0,
            penalty_breakdown=penalty_breakdown,
            efficiency_metrics=efficiency_metrics,
            timeline_metrics=timeline_metrics,
            overall_score=53.33
        )
        
        assert scoring_result.penalty_score == 10.0
        assert scoring_result.quality_score == 85.0
        assert scoring_result.efficiency_score == 85.0
        assert scoring_result.overall_score == 53.33
    
    def test_schedule_result_creation(self):
        """Test ScheduleResult creation."""
        schedule = {"test-pap": date(2024, 5, 1)}
        
        schedule_summary = ScheduleSummary(
            total_submissions=1,
            schedule_span=0,
            start_date=date(2024, 5, 1),
            end_date=date(2024, 5, 1),
            penalty_score=0.0,
            quality_score=100.0,
            efficiency_score=100.0,
            deadline_compliance=100.0,
            resource_utilization=80.0
        )
        
        schedule_metrics = ScheduleMetrics(
            makespan=0,
            avg_utilization=1.0,
            peak_utilization=1,
            total_penalty=0.0,
            compliance_rate=100.0,
            quality_score=100.0
        )
        
        validation_result = ValidationResult(
            is_valid=True,
            violations=[],
            deadline_validation={},
            dependency_validation={},
            resource_validation={},
            summary="Valid schedule"
        )
        
        penalty_breakdown = PenaltyBreakdown(
            total_penalty=0.0,
            deadline_penalties=0.0,
            dependency_penalties=0.0,
            resource_penalties=0.0
        )
        
        efficiency_metrics = EfficiencyMetrics(
            utilization_rate=80.0,
            peak_utilization=1,
            avg_utilization=1.0,
            efficiency_score=100.0
        )
        
        timeline_metrics = TimelineMetrics(
            duration_days=0,
            avg_daily_load=1.0,
            timeline_efficiency=100.0
        )
        
        scoring_result = ScoringResult(
            penalty_score=0.0,
            quality_score=100.0,
            efficiency_score=100.0,
            penalty_breakdown=penalty_breakdown,
            efficiency_metrics=efficiency_metrics,
            timeline_metrics=timeline_metrics,
            overall_score=66.67
        )
        
        schedule_result = ScheduleResult(
            schedule=schedule,
            summary=schedule_summary,
            metrics=schedule_metrics,
            tables={"monthly": []},
            validation=validation_result,
            scoring=scoring_result
        )
        
        assert schedule_result.schedule == schedule
        assert schedule_result.summary == schedule_summary
        assert schedule_result.metrics == schedule_metrics
        assert schedule_result.validation == validation_result
        assert schedule_result.scoring == scoring_result


class TestAnalysisClasses:
    """Test analytics classes."""
    
    def test_schedule_analysis(self):
        """Test ScheduleAnalysis creation."""
        from src.core.models import ScheduleAnalysis
        
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
    
    def test_schedule_distribution(self):
        """Test ScheduleDistribution creation."""
        from src.core.models import ScheduleDistribution
        
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
    
    def test_submission_type_analysis(self):
        """Test SubmissionTypeAnalysis creation."""
        from src.core.models import SubmissionTypeAnalysis
        
        analysis = SubmissionTypeAnalysis(
            type_counts={"paper": 3, "abstract": 2},
            type_percentages={"paper": 60.0, "abstract": 40.0},
            summary="More papers than abstracts",
            metadata={"total_submissions": 5}
        )
        
        assert analysis.type_counts["paper"] == 3
        assert analysis.type_percentages["paper"] == 60.0
        assert analysis.summary == "More papers than abstracts"
    
    def test_timeline_analysis(self):
        """Test TimelineAnalysis creation."""
        from src.core.models import TimelineAnalysis
        
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
    
    def test_resource_analysis(self):
        """Test ResourceAnalysis creation."""
        from src.core.models import ResourceAnalysis
        
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
