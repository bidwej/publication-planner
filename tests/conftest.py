"""Pytest configuration and shared fixtures."""

import pytest
import os
from datetime import date

from src.core.models import (
    Submission, SubmissionType, Config, Conference, ConferenceType, ConferenceRecurrence
)
from src.schedulers.greedy import GreedyScheduler


def create_mock_submission(submission_id, title, submission_type, conference_id, **kwargs):
    """Create a mock submission with all required attributes."""
    submission = Submission(
        id=submission_id,
        title=title,
        kind=submission_type,
        conference_id=conference_id,
        draft_window_months=kwargs.get('draft_window_months', 3),
        earliest_start_date=kwargs.get('earliest_start_date', date(2024, 1, 1)),
        depends_on=kwargs.get('depends_on', []),
        engineering=kwargs.get('engineering', False)
    )
    return submission


def create_mock_conference(conference_id, name, deadlines):
    """Create a mock conference with all required attributes."""
    conference = Conference(
        id=conference_id,
        name=name,
        conf_type=ConferenceType.MEDICAL,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines=deadlines
    )
    return conference


def create_mock_config(submissions, conferences):
    """Create a mock config with all required attributes."""
    config = Config(
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        submissions=submissions,
        conferences=conferences,
        blackout_dates=[],
        scheduling_options={"enable_early_abstract_scheduling": False}
    )
    return config


@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory."""
    return os.path.join(os.path.dirname(__file__), "common", "data")


@pytest.fixture
def sample_config():
    """Fixture to provide a sample config for testing."""
    # Create sample submissions
    submission1 = create_mock_submission(
        "paper1", "Test Paper 1", SubmissionType.PAPER, "conf1"
    )
    submission2 = create_mock_submission(
        "paper2", "Test Paper 2", SubmissionType.ABSTRACT, "conf2"
    )
    
    # Create sample conferences
    conference1 = create_mock_conference(
        "conf1", "Test Conference 1", 
        {SubmissionType.PAPER: date(2024, 6, 1)}
    )
    conference2 = create_mock_conference(
        "conf2", "Test Conference 2", 
        {SubmissionType.ABSTRACT: date(2024, 8, 1)}
    )
    
    return create_mock_config([submission1, submission2], [conference1, conference2])


@pytest.fixture
def empty_config():
    """Fixture to provide an empty config for testing."""
    return create_mock_config([], [])


@pytest.fixture
def sample_scheduler(sample_config):
    """Fixture to provide a sample scheduler for testing."""
    return GreedyScheduler(sample_config)