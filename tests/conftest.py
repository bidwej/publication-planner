"""Pytest configuration and shared fixtures for all tests."""

import pytest
from pathlib import Path


@pytest.fixture
def test_root_dir():
    """Fixture to provide the test root directory."""
    return Path(__file__).parent


@pytest.fixture
def project_root_dir():
    """Fixture to provide the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to provide a temporary directory for testing."""
    return tmp_path


def create_mock_submission(submission_id: str, title: str, submission_type, conference_id: str, **kwargs):
    """Create a mock submission for testing."""
    # Import here to avoid circular imports
    from src.core.models import Submission, SubmissionType
    
    if isinstance(submission_type, str):
        submission_type = SubmissionType(submission_type)
    
    return Submission(
        id=submission_id,
        title=title,
        kind=submission_type,
        conference_id=conference_id,
        **kwargs
    )


def create_mock_conference(conference_id: str, name: str, deadlines: dict, **kwargs):
    """Create a mock conference for testing."""
    # Import here to avoid circular imports
    from src.core.models import Conference, ConferenceType, ConferenceRecurrence
    
    return Conference(
        id=conference_id,
        name=name,
        conf_type=kwargs.get('conf_type', ConferenceType.ENGINEERING),
        recurrence=kwargs.get('recurrence', ConferenceRecurrence.ANNUAL),
        deadlines=deadlines
    )


def create_mock_config(submissions: list, conferences: list, **kwargs):
    """Create a mock config for testing."""
    # Import here to avoid circular imports
    from src.core.models import Config
    
    return Config(
        submissions=submissions,
        conferences=conferences,
        min_abstract_lead_time_days=kwargs.get('min_abstract_lead_time_days', 30),
        min_paper_lead_time_days=kwargs.get('min_paper_lead_time_days', 90),
        max_concurrent_submissions=kwargs.get('max_concurrent_submissions', 3),
        **kwargs
    )


@pytest.fixture
def empty_config():
    """Fixture to provide an empty configuration for testing."""
    return create_mock_config([], [])