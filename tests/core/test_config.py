"""Tests for core configuration loading."""

import pytest
import tempfile
import json
import os
from datetime import date
from core.config import load_config, _load_conferences, _load_submissions, _load_blackout_dates
from core.types import Config, SubmissionType, ConferenceType


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
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.json")
    
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
        conferences_path = os.path.join(test_data_dir, 'conferences.json')
        conferences = _load_conferences(conferences_path)
        
        assert len(conferences) > 0
        for conf in conferences:
            assert hasattr(conf, 'id')
            assert hasattr(conf, 'conf_type')
            assert hasattr(conf, 'recurrence')
            assert hasattr(conf, 'deadlines')
    
    def test_conference_with_abstract_deadline(self, test_data_dir):
        """Test conference with abstract deadline."""
        conferences_path = os.path.join(test_data_dir, 'conferences.json')
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
        conferences_path = os.path.join(test_data_dir, 'conferences.json')
        conferences = _load_conferences(conferences_path)
        
        # Find a conference with paper deadline
        conf_with_paper = next(
            (c for c in conferences if SubmissionType.PAPER in c.deadlines),
            None
        )
        if conf_with_paper:
            assert conf_with_paper.deadlines[SubmissionType.PAPER] is not None
    
    def test_conference_types(self, test_data_dir):
        """Test that conference types are properly parsed."""
        conferences_path = os.path.join(test_data_dir, 'conferences.json')
        conferences = _load_conferences(conferences_path)
        
        for conf in conferences:
            assert isinstance(conf.conf_type, ConferenceType)


class TestLoadSubmissions:
    """Test the _load_submissions function."""
    
    def test_load_valid_submissions(self, test_data_dir):
        """Test loading valid submission data."""
        mods_path = os.path.join(test_data_dir, 'mods.json')
        papers_path = os.path.join(test_data_dir, 'papers.json')
        
        # Create a minimal conferences list for testing
        from core.types import Conference, ConferenceType
        conferences = [
            Conference(
                id="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence="annual",
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=0,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000, "default_paper_penalty_per_day": 500}
        )
        
        assert len(submissions) > 0
        
        # Check that we have both mods and papers
        mods = [s for s in submissions if s.kind == SubmissionType.ABSTRACT]
        papers = [s for s in submissions if s.kind == SubmissionType.PAPER]
        
        assert len(mods) > 0, "Should have mods loaded as abstracts"
        assert len(papers) > 0, "Should have papers loaded"
    
    def test_submission_attributes(self, test_data_dir):
        """Test that submissions have all required attributes."""
        mods_path = os.path.join(test_data_dir, 'mods.json')
        papers_path = os.path.join(test_data_dir, 'papers.json')
        
        from core.types import Conference, ConferenceType
        conferences = [
            Conference(
                id="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence="annual",
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=0,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000, "default_paper_penalty_per_day": 500}
        )
        
        for submission in submissions:
            required_attrs = [
                'id', 'kind', 'title', 'earliest_start_date', 'conference_id',
                'engineering', 'depends_on', 'penalty_cost_per_day'
            ]
            
            for attr in required_attrs:
                assert hasattr(submission, attr), f"Submission missing attribute: {attr}"
    
    def test_paper_dependencies_conversion(self, test_data_dir):
        """Test that paper dependencies are properly converted."""
        mods_path = os.path.join(test_data_dir, 'mods.json')
        papers_path = os.path.join(test_data_dir, 'papers.json')
        
        from core.types import Conference, ConferenceType
        conferences = [
            Conference(
                id="ICML",
                conf_type=ConferenceType.ENGINEERING,
                recurrence="annual",
                deadlines={}
            )
        ]
        
        submissions = _load_submissions(
            mods_path=mods_path,
            papers_path=papers_path,
            conferences=conferences,
            abs_lead=0,
            pap_lead=60,
            penalty_costs={"default_mod_penalty_per_day": 1000, "default_paper_penalty_per_day": 500}
        )
        
        # Check that papers have proper dependency IDs
        papers = [s for s in submissions if s.kind == SubmissionType.PAPER]
        for paper in papers:
            for dep in paper.depends_on:
                # Dependencies should be in format "id-kind"
                assert '-' in dep, f"Dependency {dep} should contain '-' separator"


class TestLoadBlackoutDates:
    """Test the _load_blackout_dates function."""
    
    def test_load_valid_blackout_dates(self, test_data_dir):
        """Test loading valid blackout dates."""
        blackout_path = os.path.join(test_data_dir, 'blackout.json')
        blackout_dates = _load_blackout_dates(blackout_path)
        
        assert isinstance(blackout_dates, list)
        # Should have some blackout dates
        assert len(blackout_dates) > 0
        
        # All should be date objects
        for date_obj in blackout_dates:
            assert isinstance(date_obj, date)
    
    def test_blackout_dates_with_federal_holidays(self, test_data_dir):
        """Test loading blackout dates with federal holidays."""
        blackout_path = os.path.join(test_data_dir, 'blackout.json')
        blackout_dates = _load_blackout_dates(blackout_path)
        
        # Check that we have dates from 2025 and 2026
        years = {d.year for d in blackout_dates}
        assert 2025 in years or 2026 in years
    
    def test_blackout_dates_with_custom_periods(self, test_data_dir):
        """Test loading blackout dates with custom periods."""
        blackout_path = os.path.join(test_data_dir, 'blackout.json')
        blackout_dates = _load_blackout_dates(blackout_path)
        
        # Should have some dates
        assert len(blackout_dates) > 0
    
    def test_blackout_dates_file_not_found(self):
        """Test loading blackout dates from non-existent file."""
        blackout_dates = _load_blackout_dates("nonexistent_blackout.json")
        assert blackout_dates == []
    
    def test_blackout_dates_invalid_json(self):
        """Test loading blackout dates from invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            temp_path = f.name
        
        try:
            blackout_dates = _load_blackout_dates(temp_path)
            assert blackout_dates == []
        finally:
            os.unlink(temp_path)


class TestConfigIntegration:
    """Integration tests for configuration loading."""
    
    def test_full_config_loading(self, config):
        """Test that full configuration loads correctly."""
        assert config is not None
        assert len(config.submissions) > 0
        assert len(config.conferences) > 0
        
        # Check that submissions_dict is populated
        assert hasattr(config, 'submissions_dict')
        assert len(config.submissions_dict) == len(config.submissions)
        
        # Check that all submissions are in the dict
        for submission in config.submissions:
            assert submission.id in config.submissions_dict
    
    def test_config_with_blackout_periods_disabled(self):
        """Test config loading with blackout periods disabled."""
        # Create a temporary config with blackout periods disabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('''{
  "min_abstract_lead_time_days": 0,
  "min_paper_lead_time_days": 60,
  "max_concurrent_submissions": 2,
  "default_paper_lead_time_months": 3,
  "scheduling_options": {
    "enable_blackout_periods": false
  },
  "data_files": {
    "conferences": "data/conferences.json",
    "mods": "data/mods.json",
    "papers": "data/papers.json"
  }
}''')
            temp_path = f.name
        
        try:
            config = load_config(temp_path)
            assert config.blackout_dates == []
        finally:
            os.unlink(temp_path) 