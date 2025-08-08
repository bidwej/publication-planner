"""Pytest configuration and shared fixtures for all tests."""
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Any

import pytest

from src.core.models import (
    Config, Submission, Conference, SubmissionType, 
    ConferenceType, ConferenceRecurrence
)


@pytest.fixture
def test_root_dir() -> Path:
    """Fixture to provide the test root directory."""
    return Path(__file__).parent


@pytest.fixture
def project_root_dir() -> Path:
    """Fixture to provide the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Fixture to provide a temporary directory for testing."""
    return tmp_path


def create_mock_submission(
    submission_id: str, 
    title: str, 
    submission_type: Any, 
    conference_id: Optional[str], 
    **kwargs: Any
) -> Submission:
    """Create a mock submission for testing."""
    if isinstance(submission_type, str):
        submission_type = SubmissionType(submission_type)
    
    return Submission(
        id=submission_id,
        title=title,
        kind=submission_type,
        conference_id=conference_id,
        **kwargs
    )


def create_mock_conference(
    conference_id: str, 
    name: str, 
    deadlines: Dict[Any, date], 
    **kwargs: Any
) -> Conference:
    """Create a mock conference for testing."""
    return Conference(
        id=conference_id,
        name=name,
        conf_type=kwargs.get('conf_type', ConferenceType.ENGINEERING),
        recurrence=kwargs.get('recurrence', ConferenceRecurrence.ANNUAL),
        deadlines=deadlines
    )


def create_mock_config(
    submissions: Optional[List[Submission]] = None, 
    conferences: Optional[List[Conference]] = None, 
    **kwargs: Any
) -> Config:
    """Create a mock config for testing."""
    if submissions is None:
        submissions = []
    if conferences is None:
        conferences = []
    
    return Config(
        submissions=submissions,
        conferences=conferences,
        min_abstract_lead_time_days=kwargs.get('min_abstract_lead_time_days', 30),
        min_paper_lead_time_days=kwargs.get('min_paper_lead_time_days', 90),
        max_concurrent_submissions=kwargs.get('max_concurrent_submissions', 3),
        default_paper_lead_time_months=kwargs.get('default_paper_lead_time_months', 3),
        penalty_costs=kwargs.get('penalty_costs', {}),
        priority_weights=kwargs.get('priority_weights', {}),
        scheduling_options=kwargs.get('scheduling_options', {}),
        blackout_dates=kwargs.get('blackout_dates', []),
        data_files=kwargs.get('data_files', {})
    )


@pytest.fixture
def empty_config() -> Config:
    """Fixture to provide an empty configuration for testing."""
    return Config.create_default()


@pytest.fixture
def sample_config() -> Config:
    """Fixture to provide a sample configuration with test data."""
    # Create sample conferences
    sample_conferences: List[Conference] = [
        Conference(
            id="ICRA2026",
            name="IEEE International Conference on Robotics and Automation 2026",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 1, 15),
                SubmissionType.PAPER: date(2026, 2, 15)
            }
        ),
        Conference(
            id="MICCAI2026",
            name="Medical Image Computing and Computer Assisted Intervention 2026",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: date(2026, 3, 1),
                SubmissionType.PAPER: date(2026, 4, 1)
            }
        )
    ]
    
    # Create sample submissions
    sample_submissions: List[Submission] = [
        Submission(
            id="mod1-wrk",
            title="Endoscope Navigation Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="ICRA2026",
            depends_on=[],
            draft_window_months=0,
            engineering=True
        ),
        Submission(
            id="paper1-pap",
            title="AI-Powered Endoscope Control System",
            kind=SubmissionType.PAPER,
            conference_id="ICRA2026",
            depends_on=["mod1-wrk"],
            draft_window_months=3,
            engineering=True
        ),
        Submission(
            id="mod2-wrk",
            title="Medical Image Analysis Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="MICCAI2026",
            depends_on=[],
            draft_window_months=0,
            engineering=False
        ),
        Submission(
            id="paper2-pap",
            title="Deep Learning for Endoscope Guidance",
            kind=SubmissionType.PAPER,
            conference_id="MICCAI2026",
            depends_on=["mod2-wrk"],
            draft_window_months=3,
            engineering=False
        )
    ]
    
    # Default penalty costs
    default_penalty_costs: Dict[str, float] = {
        "default_mod_penalty_per_day": 1000.0,
        "default_paper_penalty_per_day": 2000.0
    }
    
    # Default priority weights
    default_priority_weights: Dict[str, float] = {
        "engineering_paper": 2.0,
        "medical_paper": 1.0,
        "mod": 1.5,
        "abstract": 0.5
    }
    
    # Default scheduling options
    default_scheduling_options: Dict[str, bool] = {
        "enable_blackout_periods": False,
        "enable_early_abstract_scheduling": False,
        "enable_working_days_only": False,
        "enable_priority_weighting": True,
        "enable_dependency_tracking": True,
        "enable_concurrency_control": True
    }
    
    return Config(
        submissions=sample_submissions,
        conferences=sample_conferences,
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        default_paper_lead_time_months=3,
        penalty_costs=default_penalty_costs,
        priority_weights=default_priority_weights,
        scheduling_options=default_scheduling_options,
        blackout_dates=[],
        data_files={
            "conferences": "conferences.json",
            "papers": "papers.json",
            "mods": "mods.json"
        }
    )