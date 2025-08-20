"""Pytest configuration and shared fixtures for all tests."""
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

import pytest

from core.models import (
    Config, Submission, Conference, SubmissionType, 
    ConferenceType, ConferenceRecurrence, Schedule, ValidationResult
)
from core.constants import QUALITY_CONSTANTS, PRIORITY_CONSTANTS, PENALTY_CONSTANTS


def build_validation_result(violations, total_submissions, compliant_submissions, summary_template):
    """Shared helper to build standardized ValidationResult objects across all validation modules."""
    compliance_rate = (compliant_submissions / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else QUALITY_CONSTANTS.perfect_compliance_rate
    
    return ValidationResult(
        is_valid=len(violations) == 0,
        violations=violations,
        summary=summary_template.format(
            compliant=compliant_submissions, 
            total=total_submissions, 
            rate=compliance_rate
        ),
        metadata={
            "compliance_rate": compliance_rate,
            "total_submissions": total_submissions,
            "compliant_submissions": compliant_submissions
        }
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
    
    # Set default author if not provided
    if 'author' not in kwargs:
        kwargs['author'] = "test"
    
    return Submission(
        id=submission_id,
        title=title,
        kind=submission_type,
        conference_id=conference_id,
        **kwargs
    )


def create_flexible_submission(
    submission_id: str,
    title: str,
    preferred_conferences: Optional[List[str]] = None,
    preferred_kinds: Optional[List[SubmissionType]] = None,
    **kwargs: Any
) -> Submission:
    """Create a submission for testing flexible assignment behavior."""
    # Set default author if not provided
    if 'author' not in kwargs:
        kwargs['author'] = "test"
    
    return Submission(
        id=submission_id,
        title=title,
        kind=SubmissionType.PAPER,  # Base type
        conference_id=None,  # No assigned conference
        preferred_conferences=preferred_conferences,
        preferred_kinds=preferred_kinds,
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
    # Use relative dates to avoid future date issues
    base_date = date.today() + timedelta(days=365)  # 1 year from now
    
    # Create sample conferences
    sample_conferences: List[Conference] = [
        Conference(
            id="ICRA2025",
            name="IEEE International Conference on Robotics and Automation 2025",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: base_date + timedelta(days=30),
                SubmissionType.PAPER: base_date + timedelta(days=60)
            }
        ),
        Conference(
            id="MICCAI2025",
            name="Medical Image Computing and Computer Assisted Intervention 2025",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.ABSTRACT: base_date + timedelta(days=90),
                SubmissionType.PAPER: base_date + timedelta(days=120)
            }
        )
    ]
    
    # Create sample submissions
    sample_submissions: List[Submission] = [
        Submission(
            id="mod1-wrk",
            title="Endoscope Navigation Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="ICRA2025",
            depends_on=[],
            draft_window_months=0,
            author="pccp"  # MODs are engineering papers
        ),
        Submission(
            id="paper1-pap",
            title="AI-Powered Endoscope Control System",
            kind=SubmissionType.PAPER,
            conference_id="ICRA2025",
            depends_on=["mod1-wrk"],
            draft_window_months=3,
            author="pccp"  # Engineering papers
        ),
        Submission(
            id="mod2-wrk",
            title="Medical Image Analysis Module",
            kind=SubmissionType.ABSTRACT,
            conference_id="MICCAI2025",
            depends_on=[],
            draft_window_months=0,
            author="ed"  # ED papers are medical papers
        ),
        Submission(
            id="paper2-pap",
            title="Deep Learning for Endoscope Guidance",
            kind=SubmissionType.PAPER,
            conference_id="MICCAI2025",
            depends_on=["mod2-wrk"],
            draft_window_months=3,
            author="ed"  # ED papers are medical papers
        ),
        Submission(
            id="poster1",
            title="Endoscope Control Interface Demo",
            kind=SubmissionType.POSTER,
            conference_id="ICRA2025",
            depends_on=["mod1-wrk"],
            draft_window_months=1,
            author="pccp"  # Engineering poster
        )
    ]
    
    # Default penalty costs - using constants
    default_penalty_costs: Dict[str, float] = {
        "default_mod_penalty_per_day": PENALTY_CONSTANTS.default_mod_penalty_per_day,
        "default_paper_penalty_per_day": PENALTY_CONSTANTS.default_paper_penalty_per_day
    }
    
    # Default priority weights - using constants
    default_priority_weights: Dict[str, float] = {
        "engineering_paper": PRIORITY_CONSTANTS.engineering_paper_weight,
        "medical_paper": PRIORITY_CONSTANTS.medical_paper_weight,
        "mod": PRIORITY_CONSTANTS.mod_weight,
        "abstract": PRIORITY_CONSTANTS.abstract_weight
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


@pytest.fixture
def empty_schedule() -> Schedule:
    """Fixture to provide an empty schedule for testing."""
    return Schedule()


@pytest.fixture
def sample_schedule() -> Schedule:
    """Fixture to provide a sample schedule for testing."""
    
    schedule = Schedule()
    schedule.add_interval("mod1-wrk", date(2024, 12, 1), duration_days=30)
    schedule.add_interval("paper1-pap", date(2025, 1, 15), duration_days=45)
    schedule.add_interval("mod2-wrk", date(2025, 1, 1), duration_days=30)
    schedule.add_interval("paper2-pap", date(2025, 2, 1), duration_days=45)
    schedule.add_interval("poster1", date(2025, 1, 30), duration_days=15)
    
    return schedule





@pytest.fixture
def test_data_dir():
    """Fixture to provide test data directory."""
    return str(Path(__file__).parent / "common" / "data")


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
            "engineering_paper": PRIORITY_CONSTANTS.engineering_paper_weight,
            "medical_paper": PRIORITY_CONSTANTS.medical_paper_weight,
            "mod": PRIORITY_CONSTANTS.mod_weight,
            "abstract": PRIORITY_CONSTANTS.abstract_weight
        },
        "penalty_costs": {
            "default_mod_penalty_per_day": PENALTY_CONSTANTS.default_mod_penalty_per_day
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
    
    return Config(
        min_abstract_lead_time_days=30,
        min_paper_lead_time_days=90,
        max_concurrent_submissions=3,
        submissions=[submission1, submission2],
        conferences=[conference1, conference2],
        blackout_dates=[],
        scheduling_options={"enable_early_abstract_scheduling": False},
        priority_weights={
            "engineering_paper": PRIORITY_CONSTANTS.engineering_paper_weight,
            "medical_paper": PRIORITY_CONSTANTS.medical_paper_weight,
            "mod": PRIORITY_CONSTANTS.mod_weight,
            "abstract": PRIORITY_CONSTANTS.abstract_weight
        },
        penalty_costs={"default_mod_penalty_per_day": PENALTY_CONSTANTS.default_mod_penalty_per_day},
        data_files={
            "conferences": "conferences.json",
            "mods": "mod_papers.json",
            "papers": "ed_papers.json"
        }
    )


@pytest.fixture 
def mock_schedule_summary():
    """Fixture to provide a mock schedule summary for testing."""
    from core.models import ScheduleMetrics
    
    return ScheduleMetrics(
        makespan=120,
        total_penalty=150.50,
        compliance_rate=90.5,
        quality_score=0.85,
        avg_utilization=0.75,
        peak_utilization=3,
        utilization_rate=0.75,
        efficiency_score=0.78,
        duration_days=120,
        avg_daily_load=0.75,
        timeline_efficiency=0.78,
        submission_count=5,
        scheduled_count=5,
        completion_rate=1.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 5, 1)
    )


