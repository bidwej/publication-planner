"""Pytest configuration and shared fixtures for src tests."""

import pytest
import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.core.models import (
    Submission, SubmissionType, Config, Conference, ConferenceType, ConferenceRecurrence
)


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
            "mods": "mod_papers.json",
            "papers": "ed_papers.json"
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
    
    mods_file = tmp_path / "mod_papers.json"
    with open(mods_file, 'w', encoding='utf-8') as f:
        json.dump(mods_data, f)
    
    papers_file = tmp_path / "ed_papers.json"
    with open(papers_file, 'w', encoding='utf-8') as f:
        json.dump(papers_data, f)
    
    return str(config_file)


@pytest.fixture
def config():
    """Fixture to provide a config for testing (alias for sample_config)."""
    # Create sample submissions
    submission1 = Submission(
        id="paper1", 
        title="Test Paper 1", 
        kind=SubmissionType.PAPER,
        conference_id="conf1",
        author="test",
        draft_window_months=3,
        earliest_start_date=date(2024, 1, 1),
        depends_on=[],
        engineering=False
    )
    submission2 = Submission(
        id="paper2", 
        title="Test Paper 2", 
        kind=SubmissionType.ABSTRACT,
        conference_id="conf2", 
        author="test",
        draft_window_months=1,
        earliest_start_date=date(2024, 1, 1),
        depends_on=[],
        engineering=False
    )
    
    # Create sample conferences
    conference1 = Conference(
        id="conf1", 
        name="Test Conference 1",
        conf_type=ConferenceType.MEDICAL,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={SubmissionType.PAPER: date(2026, 6, 1)}
    )
    conference2 = Conference(
        id="conf2", 
        name="Test Conference 2",
        conf_type=ConferenceType.MEDICAL,
        recurrence=ConferenceRecurrence.ANNUAL,
        deadlines={SubmissionType.ABSTRACT: date(2026, 8, 1)}
    )
    
    from src.core.models import Config
    return Config(
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        submissions=[submission1, submission2],
        conferences=[conference1, conference2],
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
            "mods": "mod_papers.json",
            "papers": "ed_papers.json"
        }
    )


@pytest.fixture 
def mock_schedule_summary():
    """Fixture to provide a mock schedule summary for testing."""
    from src.core.models import ScheduleSummary
    
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
