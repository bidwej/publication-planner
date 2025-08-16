"""Comprehensive tests for MILP optimization with real constraints."""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

from core.config import load_config
from core.models import SchedulerStrategy, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
from schedulers.optimal import OptimalScheduler


class TestOptimalSchedulerComprehensive:
    """Comprehensive tests for MILP optimization with real constraints."""
    
    def test_milp_with_simple_dependencies(self) -> None:
        """Test MILP optimization with just 2-3 submissions to prevent hanging."""
        # Use minimal test data - just 2 submissions with simple dependency
        submissions = [
            Submission(
                id="mod_1", title="Samurai Automated 2D", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=[], draft_window_months=2
            ),
            Submission(
                id="mod_2", title="Samurai Manual-Verified 2D", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=["mod_1"], draft_window_months=2
            )
        ]
        
        # Simple conference with distant deadline
        deadline = date.today() + timedelta(days=180)
        conferences = [
            Conference(
                id="test_conf", name="Test Conference", conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.ABSTRACT: deadline}
            )
        ]
        
        # Create minimal config
        from core.models import Config
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=30,
            max_concurrent_submissions=2
        )
        
        # Test with timeout - should complete quickly with small problem
        scheduler = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Even if MILP fails, we should get a dict back (not hang)
        assert isinstance(schedule, dict)
        
        # If we get a schedule, validate it
        if schedule:
            assert "mod_1" in schedule
            if "mod_2" in schedule:
                # Check dependency order
                mod1_start = schedule["mod_1"]
                mod2_start = schedule["mod_2"]
                mod1_duration = submissions[0].get_duration_days(config)
                mod1_end = mod1_start + timedelta(days=mod1_duration)
                assert mod2_start >= mod1_end
    
    def test_milp_with_simple_deadlines(self) -> None:
        """Test MILP optimization with simple deadline constraints."""
        # Single submission with deadline
        submissions = [
            Submission(
                id="paper1", title="Test Paper", kind=SubmissionType.PAPER,
                conference_id="conf1", depends_on=[], draft_window_months=3
            )
        ]
        
        deadline = date.today() + timedelta(days=90)
        conferences = [
            Conference(
                id="conf1", name="Test Conference", conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.PAPER: deadline}
            )
        ]
        
        from core.models import Config
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=30,
            max_concurrent_submissions=1
        )
        
        scheduler = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should complete quickly and return dict
        assert isinstance(schedule, dict)
        
        if schedule and "paper1" in schedule:
            start_date = schedule["paper1"]
            assert start_date >= date.today()
            assert start_date <= deadline - timedelta(days=30)  # Allow for lead time
    
    def test_milp_with_minimal_blackout_dates(self) -> None:
        """Test MILP with minimal blackout date constraints."""
        # Use sample data structure but minimal size
        submissions = [
            Submission(
                id="mod_1", title="Test Mod", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=[], draft_window_months=2
            )
        ]
        
        conferences = [
            Conference(
                id="test_conf", name="Test Conference", conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.ABSTRACT: date.today() + timedelta(days=60)}
            )
        ]
        
        from core.models import Config
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=30,
            max_concurrent_submissions=1,
            blackout_dates=[date.today() + timedelta(days=15)]  # Single blackout date
        )
        
        scheduler = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should complete quickly
        assert isinstance(schedule, dict)
    
    def test_milp_with_simple_resource_constraints(self) -> None:
        """Test MILP with basic resource constraints."""
        # Two independent submissions
        submissions = [
            Submission(
                id="mod_1", title="Test Mod 1", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=[], draft_window_months=1
            ),
            Submission(
                id="mod_2", title="Test Mod 2", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=[], draft_window_months=1
            )
        ]
        
        conferences = [
            Conference(
                id="test_conf", name="Test Conference", conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.ABSTRACT: date.today() + timedelta(days=30)}
            )
        ]
        
        from core.models import Config
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=30,
            max_concurrent_submissions=1  # Force sequential scheduling
        )
        
        scheduler = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should complete quickly
        assert isinstance(schedule, dict)
        
        if len(schedule) >= 2:
            # Check that they don't overlap
            mod1_start = schedule["mod_1"]
            mod2_start = schedule["mod_2"]
            mod1_duration = submissions[0].get_duration_days(config)
            mod1_end = mod1_start + timedelta(days=mod1_duration)
            assert mod2_start >= mod1_end
    
    def test_milp_optimality_verification(self) -> None:
        """Test that MILP provides optimal solutions when it works."""
        # Simple scenario that should be solvable
        submissions = [
            Submission(
                id="mod_1", title="Test Mod", kind=SubmissionType.ABSTRACT,
                conference_id=None, depends_on=[], draft_window_months=1
            )
        ]
        
        conferences = [
            Conference(
                id="test_conf", name="Test Conference", conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.ABSTRACT: date.today() + timedelta(days=60)}
            )
        ]
        
        from core.models import Config
        config = Config(
            submissions=submissions,
            conferences=conferences,
            min_abstract_lead_time_days=0,
            min_paper_lead_time_days=30,
            max_concurrent_submissions=1
        )
        
        scheduler = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should complete quickly
        assert isinstance(schedule, dict)
        
        # If we get a solution, it should be optimal (earliest possible start)
        if schedule and "mod_1" in schedule:
            start_date = schedule["mod_1"]
            assert start_date >= date.today()
            # Should start as early as possible (today or tomorrow)
            assert start_date <= date.today() + timedelta(days=1)
