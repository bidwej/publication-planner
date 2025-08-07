"""Tests for the greedy scheduler."""

from datetime import date, timedelta
from typing import Dict

import pytest

from src.core.models import SubmissionType, ConferenceType, ConferenceRecurrence
from src.schedulers.greedy import GreedyScheduler
from tests.conftest import create_mock_submission, create_mock_conference, create_mock_config


class TestGreedyScheduler:
    """Test the greedy scheduler functionality."""

    def test_greedy_scheduler_initialization(self, empty_config):
        """Test greedy scheduler initialization."""
        scheduler = GreedyScheduler(empty_config)
        
        assert scheduler.config == empty_config
        assert hasattr(scheduler, 'schedule')
        assert hasattr(scheduler, '_sort_by_priority')
        assert hasattr(scheduler, '_find_earliest_valid_start')

    def test_schedule_empty_config(self, empty_config):
        """Test scheduling with empty config."""
        scheduler = GreedyScheduler(empty_config)
        
        result = scheduler.schedule()
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_schedule_single_submission(self):
        """Test scheduling a single submission."""
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert "paper1" in result
        assert isinstance(result["paper1"], date)

    def test_schedule_with_dependencies(self):
        """Test scheduling with dependencies."""
        submission1 = create_mock_submission(
            "paper1", "Dependency Paper", SubmissionType.PAPER, "conf1"
        )
        submission2 = create_mock_submission(
            "paper2", "Dependent Paper", SubmissionType.PAPER, "conf1",
            depends_on=["paper1"]
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission1, submission2], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1
        assert "paper1" in result
        
        # If both are scheduled, check dependency constraint
        if "paper2" in result:
            # Dependent paper should start after dependency ends
            paper1_end = result["paper1"] + timedelta(days=config.min_paper_lead_time_days)
            assert result["paper2"] >= paper1_end

    def test_schedule_respects_earliest_start_date(self):
        """Test that schedule respects earliest start dates."""
        earliest_start = date(2025, 6, 1)
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=earliest_start
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        if "paper1" in result:
            assert result["paper1"] >= earliest_start

    def test_schedule_respects_deadlines(self):
        """Test that schedule respects deadlines."""
        deadline = date(2025, 6, 1)
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: deadline}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        if "paper1" in result:
            # Start date + duration should be before deadline
            end_date = result["paper1"] + timedelta(days=config.min_paper_lead_time_days)
            assert end_date <= deadline

    def test_schedule_respects_concurrency_limit(self):
        """Test that schedule respects concurrency limits."""
        submissions = []
        for i in range(5):
            submission = create_mock_submission(
                f"paper{i}", f"Test Paper {i}", SubmissionType.PAPER, "conf1"
            )
            submissions.append(submission)
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config(submissions, [conference], max_concurrent_submissions=2)
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        
        # Check that no more than max_concurrent_submissions are scheduled on the same day
        scheduled_dates = list(result.values())
        for i, date1 in enumerate(scheduled_dates):
            same_date_count = sum(1 for d in scheduled_dates if d == date1)
            assert same_date_count <= config.max_concurrent_submissions

    def test_sort_by_priority(self):
        """Test priority sorting functionality."""
        submission1 = create_mock_submission(
            "paper1", "Engineering Paper", SubmissionType.PAPER, "conf1",
            engineering=True
        )
        submission2 = create_mock_submission(
            "abstract1", "Abstract", SubmissionType.ABSTRACT, "conf1"
        )
        submission3 = create_mock_submission(
            "poster1", "Poster", SubmissionType.POSTER, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1),
             SubmissionType.ABSTRACT: date(2025, 12, 1),
             SubmissionType.POSTER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission1, submission2, submission3], [conference])
        
        scheduler = GreedyScheduler(config)
        
        # Test with default priority weights
        ready = ["paper1", "abstract1", "poster1"]
        sorted_ready = scheduler._sort_by_priority(ready)
        
        assert isinstance(sorted_ready, list)
        assert len(sorted_ready) == 3
        assert all(sid in sorted_ready for sid in ready)

    def test_sort_by_priority_with_custom_weights(self):
        """Test priority sorting with custom weights."""
        submission1 = create_mock_submission(
            "paper1", "Engineering Paper", SubmissionType.PAPER, "conf1",
            engineering=True
        )
        submission2 = create_mock_submission(
            "abstract1", "Abstract", SubmissionType.ABSTRACT, "conf1"
        )
        
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1),
             SubmissionType.ABSTRACT: date(2025, 12, 1)}
        )
        
        # Custom priority weights
        priority_weights = {
            "engineering_paper": 2.0,
            "abstract": 1.0
        }
        
        config = create_mock_config([submission1, submission2], [conference])
        config.priority_weights = priority_weights
        
        scheduler = GreedyScheduler(config)
        
        ready = ["paper1", "abstract1"]
        sorted_ready = scheduler._sort_by_priority(ready)
        
        assert isinstance(sorted_ready, list)
        assert len(sorted_ready) == 2
        # Engineering paper should have higher priority
        assert sorted_ready[0] == "paper1"

    def test_find_earliest_valid_start(self):
        """Test finding earliest valid start date."""
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        schedule = {}
        
        start_date = scheduler._find_earliest_valid_start(submission, schedule)
        
        assert isinstance(start_date, date)
        assert start_date >= date.today()

    def test_find_earliest_valid_start_with_dependencies(self):
        """Test finding earliest valid start date with dependencies."""
        submission1 = create_mock_submission(
            "paper1", "Dependency Paper", SubmissionType.PAPER, "conf1"
        )
        submission2 = create_mock_submission(
            "paper2", "Dependent Paper", SubmissionType.PAPER, "conf1",
            depends_on=["paper1"]
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission1, submission2], [conference])
        
        scheduler = GreedyScheduler(config)
        
        # Schedule dependency first
        schedule = {"paper1": date(2025, 1, 1)}
        
        start_date = scheduler._find_earliest_valid_start(submission2, schedule)
        
        assert isinstance(start_date, date)
        # Should start after dependency ends
        dependency_end = schedule["paper1"] + timedelta(days=config.min_paper_lead_time_days)
        assert start_date >= dependency_end

    def test_find_earliest_valid_start_with_earliest_start_date(self):
        """Test finding earliest valid start date with explicit earliest start date."""
        earliest_start = date(2025, 6, 1)
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=earliest_start
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        schedule = {}
        
        start_date = scheduler._find_earliest_valid_start(submission, schedule)
        
        assert isinstance(start_date, date)
        assert start_date >= earliest_start

    def test_find_earliest_valid_start_with_deadline_constraint(self):
        """Test finding earliest valid start date with deadline constraint."""
        deadline = date(2025, 6, 1)
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: deadline}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        schedule = {}
        
        start_date = scheduler._find_earliest_valid_start(submission, schedule)
        
        if start_date is not None:
            # Start date + duration should be before deadline
            end_date = start_date + timedelta(days=config.min_paper_lead_time_days)
            assert end_date <= deadline

    def test_find_earliest_valid_start_with_resource_constraints(self):
        """Test finding earliest valid start date with resource constraints."""
        submission1 = create_mock_submission(
            "paper1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        submission2 = create_mock_submission(
            "paper2", "Test Paper 2", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission1, submission2], [conference], max_concurrent_submissions=1)
        
        scheduler = GreedyScheduler(config)
        
        # Schedule first submission
        schedule = {"paper1": date(2025, 1, 1)}
        
        start_date = scheduler._find_earliest_valid_start(submission2, schedule)
        
        if start_date is not None:
            # Should start after first submission ends
            first_end = schedule["paper1"] + timedelta(days=config.min_paper_lead_time_days)
            assert start_date >= first_end

    def test_schedule_with_impossible_constraints(self):
        """Test scheduling with impossible constraints."""
        # Create submission with impossible constraints
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            earliest_start_date=date(2025, 12, 1)  # Start after deadline
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 6, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        # Should return empty schedule or skip impossible submission
        assert isinstance(result, dict)

    def test_schedule_with_abstract_and_paper(self):
        """Test scheduling with abstract and paper submissions."""
        abstract = create_mock_submission(
            "abstract1", "Test Abstract", SubmissionType.ABSTRACT, "conf1"
        )
        paper = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1",
            depends_on=["abstract1"]
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.ABSTRACT: date(2025, 10, 1),
             SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([abstract, paper], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1
        
        # If both are scheduled, check dependency constraint
        if "abstract1" in result and "paper1" in result:
            abstract_end = result["abstract1"] + timedelta(days=config.min_abstract_lead_time_days)
            assert result["paper1"] >= abstract_end

    def test_schedule_with_engineering_and_medical_papers(self):
        """Test scheduling with engineering and medical papers."""
        engineering_paper = create_mock_submission(
            "paper1", "Engineering Paper", SubmissionType.PAPER, "conf1",
            engineering=True
        )
        medical_paper = create_mock_submission(
            "paper2", "Medical Paper", SubmissionType.PAPER, "conf1",
            engineering=False
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([engineering_paper, medical_paper], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1

    def test_schedule_with_conference_assignment(self):
        """Test scheduling with conference assignment."""
        submission = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, None,  # No conference assigned
            candidate_conferences=["Test Conference"]
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission], [conference])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        # Should be able to schedule even with conference assignment

    def test_auto_link_abstract_paper(self):
        """Test auto-linking abstracts to papers."""
        abstract = create_mock_submission(
            "abstract1", "Test Abstract", SubmissionType.ABSTRACT, "conf1"
        )
        paper = create_mock_submission(
            "paper1", "Test Paper", SubmissionType.PAPER, "conf1"
        )
        conference = create_mock_conference(
            "conf1", "Test Conference", 
            {SubmissionType.ABSTRACT: date(2025, 3, 1),
             SubmissionType.PAPER: date(2025, 6, 1)}
        )
        config = create_mock_config([abstract, paper], [conference])
        
        scheduler = GreedyScheduler(config)
        
        # Should not raise any errors
        scheduler._auto_link_abstract_paper()

    def test_schedule_with_multiple_conferences(self):
        """Test scheduling with multiple conferences."""
        submission1 = create_mock_submission(
            "paper1", "Test Paper 1", SubmissionType.PAPER, "conf1"
        )
        submission2 = create_mock_submission(
            "paper2", "Test Paper 2", SubmissionType.PAPER, "conf2"
        )
        conference1 = create_mock_conference(
            "conf1", "Test Conference 1", 
            {SubmissionType.PAPER: date(2025, 6, 1)}
        )
        conference2 = create_mock_conference(
            "conf2", "Test Conference 2", 
            {SubmissionType.PAPER: date(2025, 12, 1)}
        )
        config = create_mock_config([submission1, submission2], [conference1, conference2])
        
        scheduler = GreedyScheduler(config)
        result = scheduler.schedule()
        
        assert isinstance(result, dict)
        assert len(result) >= 1
