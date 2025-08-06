"""Test configuration and fixtures for the paper planner system."""

import pytest
import os
from pathlib import Path
from datetime import date

from core.config import load_config
from core.models import (
    Config, Submission, Conference, ConferenceType, 
    ConferenceRecurrence, SubmissionType
)
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the test data directory path."""
    return os.path.join(os.path.dirname(__file__), 'common', 'data')


@pytest.fixture(scope="session")
def test_config_path(test_data_dir):
    """Provide the test config.json path."""
    return os.path.join(test_data_dir, 'config.json')


@pytest.fixture(scope="session")
def config(test_config_path):
    """Load the test configuration."""
    return load_config(test_config_path)


@pytest.fixture(scope="session")
def sample_schedule(config):
    """Generate a sample schedule for testing."""
    scheduler = GreedyScheduler(config)
    return scheduler.schedule()


@pytest.fixture
def greedy_scheduler(config):
    """Provide a greedy scheduler instance."""
    return GreedyScheduler(config)


@pytest.fixture
def stochastic_scheduler(config):
    """Provide a stochastic scheduler instance."""
    return StochasticGreedyScheduler(config)


@pytest.fixture
def lookahead_scheduler(config):
    """Provide a lookahead scheduler instance."""
    return LookaheadGreedyScheduler(config)


@pytest.fixture
def backtracking_scheduler(config):
    """Provide a backtracking scheduler instance."""
    return BacktrackingGreedyScheduler(config)


@pytest.fixture
def all_schedulers(greedy_scheduler, stochastic_scheduler, lookahead_scheduler, backtracking_scheduler):
    """Provide all scheduler instances."""
    return {
        "greedy": greedy_scheduler,
        "stochastic": stochastic_scheduler,
        "lookahead": lookahead_scheduler,
        "backtracking": backtracking_scheduler
    }


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
    from core.models import Conference, ConferenceType, ConferenceRecurrence, SubmissionType
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
    """Provide a minimal config for testing edge cases."""
    from core.models import Config, Submission, Conference, ConferenceType, ConferenceRecurrence
    from datetime import date
    
    return Config(
        submissions=[],
        conferences=[
            Conference(
                id="ICML",
                name="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={}
            )
        ],
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