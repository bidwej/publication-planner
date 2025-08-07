"""Tests for core configuration loading."""

import tempfile
from pathlib import Path
import json
from datetime import date
from dataclasses import asdict, replace
from core.config import load_config, _load_conferences, _load_submissions, _load_blackout_dates
from core.models import Config, SubmissionType, ConferenceType, SchedulerStrategy, ConferenceRecurrence, Conference


class TestLoadConfig:
    """Test the main load_config function."""
    
    def test_load_valid_config(self, test_config_path):
        """Test loading a valid configuration."""
        config = load_config(test_config_path)
        assert isinstance(config, Config)
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
    
    def test_load_config_with_blackout_dates(self, test_config_path):
        """Test loading config with blackout dates enabled."""
        config = load_config(test_config_path)
        # Check that blackout dates are loaded if enabled
        assert hasattr(config, 'blackout_dates')
        assert isinstance(config.blackout_dates, list)
    
    def test_load_config_file_not_found(self):
        """Test loading a non-existent config file."""
        # Now returns default config instead of raising FileNotFoundError
        config = load_config("nonexistent_config.json")
        assert isinstance(config, Config)
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
    
    def test_config_has_required_attributes(self, config):
        """Test that config has all required attributes."""
        required_attrs = [
            'min_abstract_lead_time_days',
            'min_paper_lead_time_days',
            'max_concurrent_submissions',
            'default_paper_lead_time_months',
            'conferences',
            'submissions',
            'data_files',
            'priority_weights',
            'penalty_costs',
            'scheduling_options',
            'blackout_dates'
        ]
        
        for attr in required_attrs:
            assert hasattr(config, attr), f"Config missing attribute: {attr}"
    
    def test_priority_weights_defaults(self, config):
        """Test that priority weights have sensible defaults."""
        weights = config.priority_weights
        assert 'engineering_paper' in weights
        assert 'medical_paper' in weights
        assert 'mod' in weights
        assert 'abstract' in weights
        assert weights['engineering_paper'] > weights['medical_paper']


class TestLoadConferences:
    """Test the _load_conferences function."""
    
    def test_load_valid_conferences(self, test_data_dir):
        """Test loading valid conference data."""
        conferences_path = Path(test_data_dir) / 'conferences.json'
        conferences = _load_conferences(conferences_path)
        
        assert len(conferences) > 0
        for conf in conferences:
            assert hasattr(conf, 'id')
            assert hasattr(conf, 'conf_type')
            assert hasattr(conf, 'recurrence')
            assert hasattr(conf, 'deadlines')
    
    def test_conference_with_abstract_deadline(self, test_data_dir):
        """Test conference with abstract deadline."""
        conferences_path = Path(test_data_dir) / 'conferences.json'
        conferences = _load_conferences(conferences_path)
        
        # Find a conference with abstract deadline
        conf_with_abstract = next(
            (c for c in conferences if SubmissionType.ABSTRACT in c.deadlines),
            None
        )
        if conf_with_abstract:
            assert conf_with_abstract.deadlines[SubmissionType.ABSTRACT] is not None
    
    def test_conference_with_paper_deadline(self, test_data_dir):
        """Test conference with paper deadline."""
        conferences_path = Path(test_data_dir) / 'conferences.json'
        conferences = _load_conferences(conferences_path)
        
        # Find a conference with paper deadline
        conf_with_paper = next(
            (c for c in conferences if SubmissionType.PAPER in c.deadlines),
            None
        )
        if conf_with_paper:
            assert conf_with_paper.deadlines[SubmissionType.PAPER] is not None
    
    def test_conference_types(self, test_data_dir):
        """Test that conferences have valid types."""
        conferences_path = Path(test_data_dir) / 'conferences.json'
        conferences = _load_conferences(conferences_path)
        
        for conf in conferences:
            assert conf.conf_type in [ConferenceType.ENGINEERING, ConferenceType.MEDICAL]
            assert conf.recurrence in [ConferenceRecurrence.ANNUAL, ConferenceRecurrence.BIENNIAL]


class TestLoadSubmissions:
    """Test the _load_submissions function."""
    
    def test_load_valid_submissions(self, test_data_dir):
        """Test loading valid submission data."""
        mods_path = Path(test_data_dir) / 'mods.json'
        papers_path = Path(test_data_dir) / 'papers.json'
        
        # Create minimal conferences for testing
        conferences = [
            Conference(
                id="test_conf",
                name="Test Conference",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=30,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000.0}
        )
        
        assert len(submissions) > 0
        for submission in submissions:
            assert hasattr(submission, 'id')
            assert hasattr(submission, 'title')
            assert hasattr(submission, 'kind')
            assert hasattr(submission, 'conference_id')
    
    def test_submission_attributes(self, test_data_dir):
        """Test that submissions have all required attributes."""
        mods_path = Path(test_data_dir) / 'mods.json'
        papers_path = Path(test_data_dir) / 'papers.json'
        
        conferences = [
            Conference(
                id="test_conf",
                name="Test Conference",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=30,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000.0}
        )
        
        for submission in submissions:
            assert submission.id.endswith(('-wrk', '-pap'))
            assert submission.title is not None
            assert submission.kind in [SubmissionType.ABSTRACT, SubmissionType.PAPER]
            assert isinstance(submission.depends_on, list)
            assert isinstance(submission.draft_window_months, int)
            assert isinstance(submission.lead_time_from_parents, int)
            assert isinstance(submission.penalty_cost_per_day, float)
            assert isinstance(submission.engineering, bool)
    
    def test_paper_dependencies_conversion(self, test_data_dir):
        """Test that paper dependencies are correctly converted."""
        mods_path = Path(test_data_dir) / 'mods.json'
        papers_path = Path(test_data_dir) / 'papers.json'
        
        conferences = [
            Conference(
                id="test_conf",
                name="Test Conference",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=30,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000.0}
        )
        
        # Check that paper submissions have correct dependency format
        paper_submissions = [s for s in submissions if s.kind == SubmissionType.PAPER]
        for paper in paper_submissions:
            for dep in paper.depends_on or []:
                assert dep.endswith(('-wrk', '-pap'))


class TestLoadBlackoutDates:
    """Test the _load_blackout_dates function."""
    
    def test_load_valid_blackout_dates(self, test_data_dir):
        """Test loading valid blackout dates."""
        blackout_path = Path(test_data_dir) / 'blackout.json'
        blackout_dates = _load_blackout_dates(blackout_path)
        
        assert isinstance(blackout_dates, list)
        for date_obj in blackout_dates:
            assert isinstance(date_obj, date)
    
    def test_blackout_dates_with_federal_holidays(self, test_data_dir):
        """Test blackout dates with federal holidays."""
        blackout_path = Path(test_data_dir) / 'blackout.json'
        blackout_dates = _load_blackout_dates(blackout_path)
        
        # Should have some federal holidays
        assert len(blackout_dates) > 0
    
    def test_blackout_dates_with_custom_periods(self, test_data_dir):
        """Test blackout dates with custom periods."""
        blackout_path = Path(test_data_dir) / 'blackout.json'
        blackout_dates = _load_blackout_dates(blackout_path)
        
        # Should have dates from custom periods
        assert len(blackout_dates) > 0
    
    def test_blackout_dates_file_not_found(self):
        """Test handling of missing blackout file."""
        # Should return empty list for non-existent file
        blackout_dates = _load_blackout_dates(Path("nonexistent.json"))
        assert blackout_dates == []
    
    def test_blackout_dates_invalid_json(self):
        """Test handling of invalid JSON in blackout file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            blackout_dates = _load_blackout_dates(Path(temp_path))
            assert blackout_dates == []
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestConfigIntegration:
    """Test integration of all config components."""
    
    def test_full_config_loading(self, config):
        """Test that all config components work together."""
        assert isinstance(config, Config)
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
        assert config.min_abstract_lead_time_days > 0
        assert config.min_paper_lead_time_days > 0
        assert config.max_concurrent_submissions > 0
    
    def test_default_config_creation(self):
        """Test that default config can be created."""
        config = Config.create_default()
        assert isinstance(config, Config)
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
        assert config.min_abstract_lead_time_days > 0
        assert config.min_paper_lead_time_days > 0
        assert config.max_concurrent_submissions > 0
    
    def test_load_config_with_nonexistent_file(self):
        """Test loading config when file doesn't exist."""
        # Should return default config instead of raising error
        config = load_config("nonexistent_file.json")
        assert isinstance(config, Config)
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
    
    def test_config_with_blackout_periods_disabled(self, test_data_dir):
        """Test config loading when blackout periods are disabled."""
        # Create a config file with blackout periods disabled
        config_data = {
            "min_abstract_lead_time_days": 30,
            "min_paper_lead_time_days": 60,
            "max_concurrent_submissions": 3,
            "data_files": {
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            },
            "scheduling_options": {
                "enable_blackout_periods": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Copy test data to temp directory
            temp_dir = Path(config_path).parent
            for filename in ['conferences.json', 'mods.json', 'papers.json']:
                src = Path(test_data_dir) / filename
                dst = temp_dir / filename
                if exists():
                    dst.write_text(read_text())
            
            config = load_config(config_path)
            assert isinstance(config, Config)
            assert len(config.blackout_dates or []) == 0  # Should be empty when disabled
            
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestEnums:
    """Test enum functionality."""
    
    def test_submission_type_enum(self):
        """Test SubmissionType enum."""
        assert SubmissionType.ABSTRACT.value == "abstract"
        assert SubmissionType.PAPER.value == "paper"
    
    def test_scheduler_strategy_enum(self):
        """Test SchedulerStrategy enum."""
        strategies = list(SchedulerStrategy)
        assert len(strategies) > 0
        assert SchedulerStrategy.GREEDY in strategies
    
    def test_conference_type_enum(self):
        """Test ConferenceType enum."""
        assert ConferenceType.ENGINEERING.value == "ENGINEERING"
        assert ConferenceType.MEDICAL.value == "MEDICAL"
    
    def test_conference_recurrence_enum(self):
        """Test ConferenceRecurrence enum."""
        assert ConferenceRecurrence.ANNUAL.value == "annual"
        assert ConferenceRecurrence.BIENNIAL.value == "biennial"


class TestDataclassesSerialization:
    """Test dataclass serialization and replacement."""
    
    def test_config_asdict_serialization(self, config):
        """Test that config can be serialized to dict."""
        config_dict = asdict(config)
        assert isinstance(config_dict, dict)
        assert 'submissions' in config_dict
        assert 'conferences' in config_dict
        assert 'min_abstract_lead_time_days' in config_dict
        assert 'min_paper_lead_time_days' in config_dict
        assert 'max_concurrent_submissions' in config_dict
    
    def test_config_replace_functionality(self, config):
        """Test that config can be modified using replace."""
        original_lead_time = config.min_abstract_lead_time_days
        modified_config = replace(config, min_abstract_lead_time_days=original_lead_time + 10)
        
        assert modified_config.min_abstract_lead_time_days == original_lead_time + 10
        assert modified_config.min_paper_lead_time_days == config.min_paper_lead_time_days
        assert modified_config.max_concurrent_submissions == config.max_concurrent_submissions
    
    def test_config_replace_multiple_fields(self, config):
        """Test replacing multiple fields in config."""
        modified_config = replace(
            config,
            min_abstract_lead_time_days=45,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=5
        )
        
        assert modified_config.min_abstract_lead_time_days == 45
        assert modified_config.min_paper_lead_time_days == 90
        assert modified_config.max_concurrent_submissions == 5
    
    def test_submission_asdict_serialization(self, config):
        """Test that submissions can be serialized."""
        for submission in config.submissions:
            submission_dict = asdict(submission)
            assert isinstance(submission_dict, dict)
            assert 'id' in submission_dict
            assert 'title' in submission_dict
            assert 'kind' in submission_dict
            assert 'conference_id' in submission_dict
    
    def test_conference_asdict_serialization(self, config):
        """Test that conferences can be serialized."""
        for conference in config.conferences:
            conference_dict = asdict(conference)
            assert isinstance(conference_dict, dict)
            assert 'id' in conference_dict
            assert 'name' in conference_dict
            assert 'conf_type' in conference_dict
            assert 'recurrence' in conference_dict
    
    def test_schedule_state_serialization(self, config):
        """Test that schedule state can be serialized."""
        # Create a simple schedule
        schedule = {}
        for i, submission in enumerate(config.submissions[:2]):
            schedule[submission.id] = date(2025, 1, 1 + i)
        
        # Test that schedule can be converted to dict
        schedule_dict = {k: v.isoformat() for k, v in schedule.items()}
        assert isinstance(schedule_dict, dict)
        assert len(schedule_dict) == 2
    
    def test_config_validation_after_replace(self, config):
        """Test that config validation works after replace."""
        # Create a modified config
        modified_config = replace(
            config,
            min_abstract_lead_time_days=config.min_abstract_lead_time_days + 5
        )
        
        # Should still be valid
        validation_errors = modified_config.validate()
        assert len(validation_errors) == 0


class TestConferenceMappingAndEngineering:
    """Test conference mapping and engineering flag inference."""
    
    def test_conference_mapping_by_family(self, tmp_path):
        """Test that conferences are mapped correctly by family."""
        # Create a minimal conferences list
        conferences_data = [
            {
                "name": "IEEE_ICRA",
                "conference_type": "ENGINEERING",
                "recurrence": "annual",
                "abstract_deadline": "2025-01-15",
                "full_paper_deadline": "2025-02-15"
            }
        ]
        
        # Create mods with candidate conferences
        mods_data = [
            {
                "id": "mod1",
                "title": "Test Mod 1",
                "candidate_conferences": ["IEEE_ICRA"],
                "est_data_ready": "2025-01-01"
            }
        ]
        
        # Create papers with dependencies
        papers_data = [
            {
                "id": "paper1",
                "title": "Test Paper 1",
                "mod_dependencies": ["mod1"],
                "candidate_conferences": ["IEEE_ICRA"],
                "earliest_start_date": "2025-01-01"
            }
        ]
        
        # Write test files
        conferences_file = tmp_path / "conferences.json"
        conferences_file.write_text(json.dumps(conferences_data))
        
        mods_file = tmp_path / "mods.json"
        mods_file.write_text(json.dumps(mods_data))
        
        papers_file = tmp_path / "papers.json"
        papers_file.write_text(json.dumps(papers_data))
        
        # Create config file
        config_data = {
            "min_abstract_lead_time_days": 30,
            "min_paper_lead_time_days": 60,
            "max_concurrent_submissions": 3,
            "data_files": {
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            }
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Load config
        config = load_config(str(config_file))
        
        # Check that submissions are mapped correctly
        mod_submission = next(s for s in config.submissions if s.id == "mod1-wrk")
        paper_submission = next(s for s in config.submissions if s.id == "paper1-pap")
        
        assert mod_submission.conference_id == "IEEE_ICRA"
        assert paper_submission.conference_id == "IEEE_ICRA"
        assert "mod1-wrk" in (paper_submission.depends_on or [])
    
    def test_engineering_flag_inference(self, tmp_path):
        """Test that engineering flag is inferred correctly."""
        # Create conferences with different types
        conferences_data = [
            {
                "name": "IEEE_ICRA",
                "conference_type": "ENGINEERING",
                "recurrence": "annual",
                "abstract_deadline": "2025-02-15"
            },
            {
                "name": "MICCAI",
                "conference_type": "MEDICAL",
                "recurrence": "annual",
                "abstract_deadline": "2025-02-15"
            }
        ]
        
        # Create mods that can go to both types
        mods_data = [
            {
                "id": "mod1",
                "title": "Test Mod 1",
                "candidate_conferences": ["IEEE_ICRA", "MICCAI"],
                "est_data_ready": "2025-01-01"
            }
        ]
        
        # Write test files
        conferences_file = tmp_path / "conferences.json"
        conferences_file.write_text(json.dumps(conferences_data))
        
        mods_file = tmp_path / "mods.json"
        mods_file.write_text(json.dumps(mods_data))
        
        papers_file = tmp_path / "papers.json"
        papers_file.write_text(json.dumps([]))
        
        # Create config file
        config_data = {
            "min_abstract_lead_time_days": 30,
            "min_paper_lead_time_days": 60,
            "max_concurrent_submissions": 3,
            "data_files": {
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            }
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Load config
        config = load_config(str(config_file))
        
        # Check that engineering flag is inferred correctly
        mod_submission = next(s for s in config.submissions if s.id == "mod1-wrk")
        # Should be engineering since it can go to engineering conferences
        assert mod_submission.engineering is True
    
    def test_duration_calculation_from_config(self, tmp_path):
        """Test that duration can be calculated from config."""
        # Create a simple config with known dates
        conferences_data = [
            {
                "name": "TEST_CONF",
                "conference_type": "ENGINEERING",
                "recurrence": "annual",
                "abstract_deadline": "2025-03-15",
                "full_paper_deadline": "2025-04-15"
            }
        ]
        
        mods_data = [
            {
                "id": "mod1",
                "title": "Test Mod 1",
                "conference_id": "TEST_CONF",
                "est_data_ready": "2025-01-01"
            }
        ]
        
        # Write test files
        conferences_file = tmp_path / "conferences.json"
        conferences_file.write_text(json.dumps(conferences_data))
        
        mods_file = tmp_path / "mods.json"
        mods_file.write_text(json.dumps(mods_data))
        
        papers_file = tmp_path / "papers.json"
        papers_file.write_text(json.dumps([]))
        
        # Create config file
        config_data = {
            "min_abstract_lead_time_days": 30,
            "min_paper_lead_time_days": 60,
            "max_concurrent_submissions": 3,
            "data_files": {
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            }
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Load config
        config = load_config(str(config_file))
        
        # Check that we can calculate duration
        conference = next(c for c in config.conferences if c.id == "TEST_CONF")
        abstract_deadline = conference.deadlines[SubmissionType.ABSTRACT]
        paper_deadline = conference.deadlines[SubmissionType.PAPER]
        
        duration = (paper_deadline - abstract_deadline).days
        assert duration > 0
        assert duration == 31  # March 15 to April 15 