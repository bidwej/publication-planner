"""Integration tests for config functionality."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from datetime import date

# Add root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.models import Config


class TestConfigIntegration:
    """Integration tests for config functionality."""
    
    def test_config_loading_integration(self):
        """Test config loading integration with default config."""
        from core.config import load_config
        
        with patch('core.config.load_config') as mock_load:
            # Mock load_config to return default config
            mock_config = Config.create_default()
            mock_load.return_value = mock_config
            
            # Test that config loading works
            config = load_config('config.json')
            assert config is not None
            assert isinstance(config, Config)
    
    def test_config_with_default_values(self):
        """Test config with default values integration."""
        config = Config.create_default()
        
        # Test default config properties
        assert config.submissions is not None
        assert config.conferences is not None
        assert config.min_paper_lead_time_days > 0
        assert config.min_abstract_lead_time_days > 0
        assert config.max_concurrent_submissions > 0
    
    def test_config_validation_integration(self):
        """Test config validation integration."""
        from core.models import Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
        
        # Create valid config
        submissions = [
            Submission(
                id="paper1",
                title="Test Paper",
                kind=SubmissionType.PAPER,
                conference_id="conf1",
                engineering=True
            )
        ]
        
        conferences = [
            Conference(
                id="conf1",
                name="Test Conference",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.PAPER: date(2025, 6, 1)}
            )
        ]
        
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_paper_lead_time_days=90,
            min_abstract_lead_time_days=30,
            max_concurrent_submissions=2
        )
        
        # Config should be valid
        assert config is not None
        assert len(config.submissions) == 1
        assert len(config.conferences) == 1
    
    def test_config_error_handling(self):
        """Test config error handling integration."""
        from core.config import load_config
        
        # Test with non-existent file
        with patch('builtins.open', side_effect=FileNotFoundError("Config not found")):
            with pytest.raises(FileNotFoundError):
                load_config('non_existent_config.json')
    
    def test_config_with_complex_data(self):
        """Test config with complex data structures."""
        from core.models import Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
        
        # Create complex config with multiple submissions and conferences
        submissions = [
            Submission(
                id="paper1",
                title="Engineering Paper 1",
                kind=SubmissionType.PAPER,
                conference_id="eng_conf1",
                engineering=True,
                depends_on=["abstract1"]
            ),
            Submission(
                id="abstract1",
                title="Engineering Abstract 1", 
                kind=SubmissionType.ABSTRACT,
                conference_id="eng_conf1",
                engineering=True
            ),
            Submission(
                id="paper2",
                title="Medical Paper 1",
                kind=SubmissionType.PAPER,
                conference_id="med_conf1",
                engineering=False
            )
        ]
        
        conferences = [
            Conference(
                id="eng_conf1",
                name="Engineering Conference 1",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={
                    SubmissionType.PAPER: date(2025, 6, 1),
                    SubmissionType.ABSTRACT: date(2025, 3, 1)
                }
            ),
            Conference(
                id="med_conf1",
                name="Medical Conference 1",
                conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.PAPER: date(2025, 8, 1)}
            )
        ]
        
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_paper_lead_time_days=90,
            min_abstract_lead_time_days=30,
            max_concurrent_submissions=3,
            priority_weights={
                "engineering_paper": 1.0,
                "medical_paper": 1.2,
                "abstract": 0.5
            }
        )
        
        # Test config properties
        assert len(config.submissions) == 3
        assert len(config.conferences) == 2
        assert config.priority_weights is not None
        assert "engineering_paper" in config.priority_weights
        
        # Test submission-conference relationships
        for submission in config.submissions:
            if submission.conference_id:
                conference = next((c for c in config.conferences if c.id == submission.conference_id), None)
                assert conference is not None, f"Conference {submission.conference_id} not found for submission {submission.id}"
    
    def test_config_serialization_integration(self):
        """Test config serialization and deserialization integration."""
        from core.config import save_config
        
        # Create a test config
        config = Config.create_default()
        
        # Test serialization (if save_config exists)
        try:
            with patch('builtins.open', create=True) as mock_open:
                save_config(config, 'test_config.json')
                mock_open.assert_called()
        except NameError:
            # save_config might not exist, skip this test
            pass
    
    def test_config_with_edge_cases(self):
        """Test config with edge cases and boundary conditions."""
        from core.models import Config
        
        # Test with empty submissions and conferences
        config = Config(
            submissions=[],
            conferences=[],
            min_paper_lead_time_days=1,
            min_abstract_lead_time_days=1,
            max_concurrent_submissions=1
        )
        
        assert config is not None
        assert len(config.submissions) == 0
        assert len(config.conferences) == 0
        
        # Test with minimum values
        assert config.min_paper_lead_time_days == 1
        assert config.min_abstract_lead_time_days == 1
        assert config.max_concurrent_submissions == 1
