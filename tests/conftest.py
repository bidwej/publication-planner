"""Test configuration and fixtures."""

import pytest
import os
from datetime import date

from core.models import (
    Submission, SubmissionType, Config, Conference, ConferenceType, ConferenceRecurrence
)
from schedulers.greedy import GreedyScheduler


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the test data directory path."""
    return os.path.join(os.path.dirname(__file__), 'common', 'data')


@pytest.fixture(scope="session")
def test_config_path(test_data_dir):
    """Provide the test config.json path."""
    return os.path.join(test_data_dir, 'config.json')


@pytest.fixture(scope="function")
def config():
    """Provide a full configuration for testing."""
    # Create test conferences with realistic deadlines
    conferences = [
        Conference(
            id="ICML",
            name="ICML",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2025, 1, 15),
                SubmissionType.PAPER: date(2025, 1, 30)
            }
        ),
        Conference(
            id="MICCAI",
            name="MICCAI",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2025, 2, 15),
                SubmissionType.PAPER: date(2025, 4, 1)  # Extended deadline
            }
        )
    ]
    
    # Create test submissions that can actually be scheduled
    submissions = [
        Submission(
            id="J1-pap",
            title="Test Paper",
            kind=SubmissionType.PAPER,
            conference_id="ICML",
            depends_on=[],
            draft_window_months=2,
            lead_time_from_parents=0,
            penalty_cost_per_day=500,
            engineering=True,
            earliest_start_date=date(2024, 11, 1)  # Early enough to meet deadline
        ),
        Submission(
            id="J2-pap",
            title="Medical Paper",
            kind=SubmissionType.PAPER,
            conference_id="MICCAI",
            depends_on=["J1-pap"],
            draft_window_months=3,
            lead_time_from_parents=1,  # Reduced from 2 to 1 month
            penalty_cost_per_day=300,
            engineering=False,
            earliest_start_date=date(2024, 12, 1)  # Early enough to meet deadline
        )
    ]
    
    return Config(
        submissions=submissions,
        conferences=conferences,
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=60,
        max_concurrent_submissions=2,
        default_paper_lead_time_months=3,
        penalty_costs={
            "default_mod_penalty_per_day": 1000,
            "default_paper_penalty_per_day": 500
        },
        priority_weights={
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        scheduling_options={
            "enable_early_abstract_scheduling": True,
            "abstract_advance_days": 30
        },
        blackout_dates=[],
        data_files={}
    )


@pytest.fixture(scope="function")
def sample_schedule(config):
    """Generate a sample schedule for testing."""
    scheduler = GreedyScheduler(config)
    return scheduler.schedule()


@pytest.fixture
def scheduler(config):
    """Provide a scheduler instance."""
    return GreedyScheduler(config)


@pytest.fixture
def sample_submission():
    """Provide a sample submission for testing."""
    return Submission(
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


@pytest.fixture
def sample_conference():
    """Provide a sample conference for testing."""
    from datetime import date
    
    return Conference(
        id="ICML",
        name="ICML",
        conf_type=ConferenceType.ENGINEERING,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={
            SubmissionType.ABSTRACT: date(2025, 1, 15),
            SubmissionType.PAPER: date(2025, 1, 30)
        }
    )


@pytest.fixture
def empty_schedule():
    """Provide an empty schedule for testing."""
    return {}


@pytest.fixture
def minimal_config():
    """Provide a minimal configuration for testing."""
    return Config(
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