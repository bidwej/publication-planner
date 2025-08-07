"""Pytest configuration and shared fixtures for src tests."""

import pytest
import json
from datetime import date
from pathlib import Path

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
        scheduling_options={"enable_early_abstract_scheduling": False},
        priority_weights={
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        penalty_costs={"default_mod_penalty_per_day": 1000},
        data_files={
            "conferences": "conferences.json",
            "mods": "mods.json",
            "papers": "papers.json"
        }
    )
    return config


@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory."""
    return str(Path(__file__).parent.parent / "common" / "data")


@pytest.fixture
def test_config_path(tmp_path):
    """Fixture to provide a temporary config file for testing."""
    config_data = {
        "min_abstract_lead_time_days": 30,
        "min_paper_lead_time_days": 90,
        "max_concurrent_submissions": 3,
        "default_paper_lead_time_months": 3,
        "data_files": {
            "conferences": "conferences.json",
            "mods": "mods.json",
            "papers": "papers.json"
        },
        "priority_weights": {
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        },
        "penalty_costs": {
            "default_mod_penalty_per_day": 1000
        },
        "scheduling_options": {
            "enable_blackout_periods": False,
            "enable_early_abstract_scheduling": False
        }
    }
    
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)
    
    # Create the referenced data files
    conferences_data = [
        {
            "name": "ICML",
            "conference_type": "ENGINEERING",
            "recurrence": "annual",
            "abstract_deadline": "2024-05-01",
            "full_paper_deadline": "2024-06-01"
        }
    ]
    
    mods_data = [
        {
            "id": "mod1",
            "title": "Test Mod 1",
            "conference_id": "ICML",
            "deadline": "2024-05-01",
            "draft_window_months": 1,
            "est_data_ready": "2024-01-01"
        }
    ]
    
    papers_data = [
        {
            "id": "paper1",
            "title": "Test Paper 1",
            "conference_id": "ICML",
            "deadline": "2024-06-01",
            "draft_window_months": 3,
            "mod_dependencies": [],
            "parent_papers": []
        }
    ]
    
    # Write the data files
    conferences_file = tmp_path / "conferences.json"
    with open(conferences_file, 'w', encoding='utf-8') as f:
        json.dump(conferences_data, f)
    
    mods_file = tmp_path / "mods.json"
    with open(mods_file, 'w', encoding='utf-8') as f:
        json.dump(mods_data, f)
    
    papers_file = tmp_path / "papers.json"
    with open(papers_file, 'w', encoding='utf-8') as f:
        json.dump(papers_data, f)
    
    return str(config_file)


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
        {SubmissionType.PAPER: date(2026, 6, 1)}
    )
    conference2 = create_mock_conference(
        "conf2", "Test Conference 2", 
        {SubmissionType.ABSTRACT: date(2026, 8, 1)}
    )
    
    return create_mock_config([submission1, submission2], [conference1, conference2])


@pytest.fixture
def config(sample_config):
    """Alias for sample_config to match test expectations."""
    return sample_config


@pytest.fixture
def empty_config():
    """Fixture to provide an empty config for testing."""
    return create_mock_config([], [])


@pytest.fixture
def minimal_config():
    """Fixture to provide a minimal config for testing."""
    # Create minimal submissions
    submission1 = create_mock_submission(
        "test-pap", "Test Paper", SubmissionType.PAPER, "conf1"
    )
    
    # Create minimal conference
    conference1 = create_mock_conference(
        "conf1", "Test Conference", 
        {SubmissionType.PAPER: date(2026, 6, 1)}
    )
    
    return create_mock_config([submission1], [conference1])


@pytest.fixture
def empty_schedule():
    """Fixture to provide an empty schedule for testing."""
    return {}


@pytest.fixture
def sample_schedule():
    """Fixture to provide a sample schedule for testing."""
    return {
        "paper1": date(2024, 5, 1),
        "paper2": date(2024, 7, 1)
    }


@pytest.fixture
def sample_scheduler(sample_config):
    """Fixture to provide a sample scheduler for testing."""
    return GreedyScheduler(sample_config)


@pytest.fixture
def mock_schedule_summary():
    """Fixture to provide a mock schedule summary for testing."""
    from core.models import ScheduleSummary
    
    return ScheduleSummary(
        total_submissions=5,
        schedule_span=120,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 5, 1),
        penalty_score=150.50,
        quality_score=0.85,
        efficiency_score=0.78,
        deadline_compliance=90.5,
        resource_utilization=0.75
    )
