"""Tests for core models."""

import pytest
from datetime import date
from typing import Dict
from src.core.models import (
    Config, Submission, Conference, ConferenceType, 
    ConferenceRecurrence, SubmissionType, SchedulerStrategy,
    ScheduleAnalysis, ScheduleDistribution, SubmissionTypeAnalysis,
    TimelineAnalysis, ResourceAnalysis, AnalyticsResult
)


class TestScheduleType:
    """Test Dict[str, date] schedule type."""
    
    def test_schedule_type(self):
        """Test that Dict[str, date] schedule type works correctly."""
        # Test that schedule is a valid type
        schedule: Dict[str, date] = {"paper1": date(2025, 1, 1), "paper2": date(2025, 1, 15)}
        
        assert isinstance(schedule, dict)
        assert len(schedule) == 2
        assert schedule["paper1"] == date(2025, 1, 1)
        assert schedule["paper2"] == date(2025, 1, 15)
        
        # Test that all values are dates
        for submission_id, start_date in schedule.items():
            assert isinstance(submission_id, str)
            assert isinstance(start_date, date)


class TestEnums:
    """Test enum classes."""
    
    def test_submission_type_enum(self):
        """Test SubmissionType enum values."""
        assert SubmissionType.ABSTRACT.value == "abstract"
        assert SubmissionType.PAPER.value == "paper"
        
        # Test string conversion
        assert str(SubmissionType.ABSTRACT) == "SubmissionType.ABSTRACT"
        assert str(SubmissionType.PAPER) == "SubmissionType.PAPER"
    
    def test_conference_type_enum(self):
        """Test ConferenceType enum values."""
        assert ConferenceType.ENGINEERING.value == "ENGINEERING"
        assert ConferenceType.MEDICAL.value == "MEDICAL"
        
        # Test string conversion
        assert str(ConferenceType.ENGINEERING) == "ConferenceType.ENGINEERING"
        assert str(ConferenceType.MEDICAL) == "ConferenceType.MEDICAL"
    
    def test_conference_recurrence_enum(self):
        """Test ConferenceRecurrence enum values."""
        assert ConferenceRecurrence.ANNUAL.value == "annual"
        assert ConferenceRecurrence.BIENNIAL.value == "biennial"
        
        # Test string conversion
        assert str(ConferenceRecurrence.ANNUAL) == "ConferenceRecurrence.ANNUAL"
        assert str(ConferenceRecurrence.BIENNIAL) == "ConferenceRecurrence.BIENNIAL"
    
    def test_scheduler_strategy_enum(self):
        """Test SchedulerStrategy enum values."""
        assert SchedulerStrategy.GREEDY.value == "greedy"
        assert SchedulerStrategy.STOCHASTIC.value == "stochastic"
        assert SchedulerStrategy.LOOKAHEAD.value == "lookahead"
        assert SchedulerStrategy.BACKTRACKING.value == "backtracking"
        
        # Test string conversion
        assert str(SchedulerStrategy.GREEDY) == "SchedulerStrategy.GREEDY"
        assert str(SchedulerStrategy.STOCHASTIC) == "SchedulerStrategy.STOCHASTIC"


class TestSubmission:
    """Test Submission data class."""
    
    def test_submission_creation(self):
        """Test creating a submission."""
        submission = Submission(
            id="test-pap",
            kind=SubmissionType.PAPER,
            title="Test Paper",
            earliest_start_date=date(2025, 1, 1),
            conference_id="ICML",
            engineering=True,
            depends_on=[],
            penalty_cost_per_day=500.0,
            lead_time_from_parents=0,
            draft_window_months=2
        )
        
        assert submission.id == "test-pap"
        assert submission.kind == SubmissionType.PAPER
        assert submission.title == "Test Paper"
        assert submission.earliest_start_date == date(2025, 1, 1)
        assert submission.conference_id == "ICML"
        assert submission.engineering is True
        assert submission.depends_on == []
        assert submission.penalty_cost_per_day == 500.0
        assert submission.lead_time_from_parents == 0
        assert submission.draft_window_months == 2
    
    def test_submission_with_dependencies(self):
        """Test creating a submission with dependencies."""
        submission = Submission(
            id="test-pap",
            kind=SubmissionType.PAPER,
            title="Test Paper",
            earliest_start_date=date(2025, 1, 1),
            conference_id="ICML",
            engineering=True,
            depends_on=["parent-pap"],
            penalty_cost_per_day=500.0,
            lead_time_from_parents=1,
            draft_window_months=2
        )
        
        assert submission.depends_on == ["parent-pap"]
        assert submission.lead_time_from_parents == 1
    
    def test_submission_defaults(self):
        """Test submission with default values."""
        submission = Submission(
            id="test-pap",
            kind=SubmissionType.PAPER,
            title="Test Paper",
            earliest_start_date=date(2025, 1, 1),
            conference_id="ICML"
        )
        
        assert submission.engineering is False
        assert submission.depends_on == []
        assert submission.penalty_cost_per_day is None  # Default is None, not 0.0
        assert submission.lead_time_from_parents == 0
        assert submission.draft_window_months == 3  # Default is 3, not 0


class TestConference:
    """Test Conference data class."""
    
    def test_conference_creation(self):
        """Test creating a conference."""
        conference = Conference(
            id="ICML",
            name="ICML",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2025, 1, 15),
                SubmissionType.PAPER: date(2025, 1, 30)
            }
        )
        
        assert conference.id == "ICML"
        assert conference.name == "ICML"
        assert conference.conf_type == ConferenceType.ENGINEERING
        assert conference.recurrence == ConferenceRecurrence.ANNUAL
        assert len(conference.deadlines) == 2
        assert conference.deadlines[SubmissionType.ABSTRACT] == date(2025, 1, 15)
        assert conference.deadlines[SubmissionType.PAPER] == date(2025, 1, 30)
    
    def test_conference_with_single_deadline(self):
        """Test conference with only paper deadline."""
        conference = Conference(
            id="ICML",
            name="ICML",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.PAPER: date(2025, 1, 30)
            }
        )
        
        assert len(conference.deadlines) == 1
        assert SubmissionType.PAPER in conference.deadlines
        assert SubmissionType.ABSTRACT not in conference.deadlines


class TestConfig:
    """Test Config data class."""
    
    def test_config_creation(self):
        """Test creating a config."""
        config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=60,
            max_concurrent_submissions=1,
            default_paper_lead_time_months=3,
            penalty_costs={},
            priority_weights={},
            scheduling_options={},
            blackout_dates=[],
            data_files={}
        )
        
        assert config.submissions == []
        assert config.conferences == []
        assert config.min_abstract_lead_time_days == 0
        assert config.min_paper_lead_time_days == 60
        assert config.max_concurrent_submissions == 1
        assert config.default_paper_lead_time_months == 3
        assert config.penalty_costs == {}
        assert config.priority_weights == {}
        assert config.scheduling_options == {}
        assert config.blackout_dates == []
        assert config.data_files == {}


class TestAnalysisClasses:
    """Test analysis data classes."""
    
    def test_schedule_analysis(self):
        """Test ScheduleAnalysis."""
        analysis = ScheduleAnalysis(
            scheduled_count=5,
            total_count=10,
            completion_rate=50.0,
            missing_submissions=[{"id": "sub1"}, {"id": "sub2"}],
            summary="Test summary"
        )
        
        assert analysis.scheduled_count == 5
        assert analysis.total_count == 10
        assert analysis.completion_rate == 50.0
        assert len(analysis.missing_submissions) == 2
        assert analysis.summary == "Test summary"
    
    def test_schedule_distribution(self):
        """Test ScheduleDistribution."""
        analysis = ScheduleDistribution(
            monthly_distribution={"2025-01": 3, "2025-02": 2},
            quarterly_distribution={"2025-Q1": 5},
            yearly_distribution={"2025": 5},
            summary="Test summary"
        )
        
        assert analysis.monthly_distribution == {"2025-01": 3, "2025-02": 2}
        assert analysis.quarterly_distribution == {"2025-Q1": 5}
        assert analysis.yearly_distribution == {"2025": 5}
        assert analysis.summary == "Test summary"
    
    def test_submission_type_analysis(self):
        """Test SubmissionTypeAnalysis."""
        analysis = SubmissionTypeAnalysis(
            type_counts={SubmissionType.PAPER: 3, SubmissionType.ABSTRACT: 2},
            type_percentages={SubmissionType.PAPER: 60.0, SubmissionType.ABSTRACT: 40.0},
            summary="Test summary"
        )
        
        assert analysis.type_counts == {SubmissionType.PAPER: 3, SubmissionType.ABSTRACT: 2}
        assert analysis.type_percentages == {SubmissionType.PAPER: 60.0, SubmissionType.ABSTRACT: 40.0}
        assert analysis.summary == "Test summary"
    
    def test_timeline_analysis(self):
        """Test TimelineAnalysis."""
        analysis = TimelineAnalysis(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            duration_days=364,
            avg_submissions_per_month=2.5,
            summary="Test timeline"
        )
        
        assert analysis.start_date == date(2025, 1, 1)
        assert analysis.end_date == date(2025, 12, 31)
        assert analysis.duration_days == 364
        assert analysis.avg_submissions_per_month == 2.5
        assert analysis.summary == "Test timeline"
    
    def test_resource_analysis(self):
        """Test ResourceAnalysis."""
        analysis = ResourceAnalysis(
            peak_load=5,
            avg_load=3.2,
            utilization_pattern={date(2025, 1, 1): 4, date(2025, 1, 2): 3},
            summary="Test resources"
        )
        
        assert analysis.peak_load == 5
        assert analysis.avg_load == 3.2
        assert len(analysis.utilization_pattern) == 2
        assert analysis.summary == "Test resources"
