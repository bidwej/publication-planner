"""Test configuration and fixtures for the paper planner system."""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.config import load_config
from core.types import Config, Submission, Conference
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide the test data directory path."""
    return os.path.join(os.path.dirname(__file__), 'data')


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
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('''{
  "min_abstract_lead_time_days": 0,
  "min_paper_lead_time_days": 60,
  "max_concurrent_submissions": 2,
  "default_paper_lead_time_months": 3,
  "priority_weights": {
    "engineering_paper": 2.0,
    "medical_paper": 1.0,
    "mod": 1.5,
    "abstract": 0.5
  },
  "penalty_costs": {
    "default_mod_penalty_per_day": 1000,
    "default_paper_penalty_per_day": 500
  },
  "scheduling_options": {
    "enable_early_abstract_scheduling": true,
    "abstract_advance_days": 30,
    "enable_blackout_periods": true,
    "conference_response_time_days": 90
  },
  "data_files": {
    "conferences": "data/conferences.json",
    "mods": "data/mods.json",
    "papers": "data/papers.json",
    "blackouts": "data/blackout.json"
  }
}''')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def sample_submission():
    """Provide a sample submission for testing."""
    from core.types import Submission, SubmissionType
    from datetime import date
    
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
    from core.types import Conference, ConferenceType
    from datetime import date
    
    return Conference(
        id="ICML",
        conf_type=ConferenceType.ENGINEERING,
        recurrence="annual",
        deadlines={
            "ABSTRACT": date(2025, 1, 15),
            "PAPER": date(2025, 1, 30)
        }
    )


@pytest.fixture
def empty_schedule():
    """Provide an empty schedule for testing."""
    return {}


@pytest.fixture
def minimal_config():
    """Provide a minimal config for testing edge cases."""
    from core.types import Config, Submission, Conference
    from datetime import date
    
    return Config(
        min_abstract_lead_time_days=0,
        min_paper_lead_time_days=60,
        max_concurrent_submissions=1,
        default_paper_lead_time_months=3,
        conferences=[],
        submissions=[],
        data_files={},
        priority_weights={},
        penalty_costs={},
        scheduling_options={},
        blackout_dates=[]
    )