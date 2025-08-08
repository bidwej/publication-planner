"""Integration tests for scheduler functionality."""

import pytest
import subprocess
from pathlib import Path
from datetime import date

from core.models import SchedulerStrategy
from typing import Dict, List, Any, Optional


# Import scheduler implementations to register them
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.schedulers.lookahead import LookaheadGreedyScheduler
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.schedulers.random import RandomScheduler
from src.schedulers.heuristic import HeuristicScheduler
from src.schedulers.optimal import OptimalScheduler

# Verify registration worked
from src.schedulers.base import BaseScheduler


class TestSchedulerIntegration:
    """Integration tests for scheduler functionality."""
    
    def test_scheduler_creation_with_all_strategies(self) -> None:
        """Test that all scheduler strategies can be created successfully."""
        from src.schedulers.base import BaseScheduler
        from src.core.models import Config
        
        # Create a minimal config for testing
        config = Config.create_default()
        
        # Test each strategy
        strategies = [
            SchedulerStrategy.GREEDY,
            SchedulerStrategy.STOCHASTIC,
            SchedulerStrategy.LOOKAHEAD,
            SchedulerStrategy.BACKTRACKING,
            SchedulerStrategy.RANDOM,
            SchedulerStrategy.HEURISTIC,
            SchedulerStrategy.OPTIMAL
        ]
        
        for strategy in strategies:
            try:
                scheduler: Any = BaseScheduler.create_scheduler(strategy, config)
                assert scheduler is not None
                assert hasattr(scheduler, 'schedule')
            except Exception as e:
                pytest.fail(f"Failed to create scheduler for strategy {strategy}: {e}")
    
    def test_scheduler_schedule_generation(self) -> None:
        """Test that schedulers can generate valid schedules."""
        from src.schedulers.base import BaseScheduler
        from src.core.models import Config
        
        config = Config.create_default()
        strategy = SchedulerStrategy.GREEDY
        
        scheduler: Any = BaseScheduler.create_scheduler(strategy, config)
        schedule = scheduler.schedule()
        
        # Schedule should be a dictionary
        assert isinstance(schedule, dict)
        
        # All dates should be valid
        for submission_id, start_date in schedule.items():
            assert isinstance(start_date, date)
            assert start_date >= date(2020, 1, 1)  # Reasonable start date (using our robust calculation)
    
    def test_scheduler_error_handling(self) -> None:
        """Test scheduler error handling with invalid configurations."""
        from src.schedulers.base import BaseScheduler
        from src.core.models import Config
        
        # Test with empty config
        config = Config.create_default()
        config.submissions = []  # Empty submissions
        
        strategy = SchedulerStrategy.GREEDY
        scheduler: Any = BaseScheduler.create_scheduler(strategy, config)
        schedule = scheduler.schedule()
        
        # Should return empty schedule for empty config
        assert schedule == {}
    
    def test_scheduler_strategy_comparison(self) -> None:
        """Test comparing different scheduler strategies."""
        from src.schedulers.base import BaseScheduler
        from src.core.models import Config
        
        config = Config.create_default()
        
        # Test multiple strategies
        strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.RANDOM]
        schedules = {}
        
        for strategy in strategies:
            scheduler: Any = BaseScheduler.create_scheduler(strategy, config)
            schedule = scheduler.schedule()
            schedules[strategy] = schedule
            
            # Each schedule should be valid
            assert isinstance(schedule, dict)
        
        # Different strategies might produce different schedules
        # (though with same config, they might be similar)
        assert len(schedules) == len(strategies)
    
    def test_scheduler_with_complex_constraints(self) -> None:
        """Test scheduler with complex constraints."""
        from datetime import date
        from src.schedulers.base import BaseScheduler
        from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence
        
        # Create a more complex config
        submissions = [
            Submission(
                id="paper1",
                title="Test Paper 1",
                kind=SubmissionType.PAPER,
                conference_id="conf1",
                engineering=True
            ),
            Submission(
                id="paper2", 
                title="Test Paper 2",
                kind=SubmissionType.PAPER,
                conference_id="conf2",
                engineering=False
            )
        ]
        
        conferences = [
            Conference(
                id="conf1",
                name="Engineering Conference",
                conf_type=ConferenceType.ENGINEERING,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.PAPER: date(2025, 12, 1)}
            ),
            Conference(
                id="conf2",
                name="Medical Conference", 
                conf_type=ConferenceType.MEDICAL,
                recurrence=ConferenceRecurrence.ANNUAL,
                deadlines={SubmissionType.PAPER: date(2026, 3, 1)}
            )
        ]
        
        config: Config = Config(
            submissions=submissions,
            conferences=conferences,
            min_paper_lead_time_days=90,
            min_abstract_lead_time_days=30,
            max_concurrent_submissions=2
        )
        
        # Test with different strategies
        strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.HEURISTIC]
        
        for strategy in strategies:
            scheduler: Any = BaseScheduler.create_scheduler(strategy, config)
            schedule = scheduler.schedule()
            
            # Should schedule all submissions
            assert len(schedule) == len(submissions)
            
            # All scheduled dates should be valid
            for submission_id, start_date in schedule.items():
                assert isinstance(start_date, date)
                assert start_date >= date(2025, 1, 1)
    
    def test_scheduler_subprocess_integration(self) -> None:
        """Test scheduler functionality via subprocess calls."""
        try:
            # Test help command
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent,
                timeout=10
            )
            
            assert result.returncode == 0, "Help command should succeed"
            assert "--strategy" in result.stdout
            assert "--compare" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("Scheduler subprocess test timed out")
        except Exception as e:
            pytest.fail(f"Scheduler subprocess test failed: {e}")
    
    def test_scheduler_list_strategies_subprocess(self) -> None:
        """Test list-strategies command via subprocess."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--list-strategies"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent,
                timeout=10
            )
            
            assert result.returncode == 0, "List strategies command should succeed"
            assert "greedy" in result.stdout.lower() or "available" in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.fail("List strategies subprocess test timed out")
        except Exception as e:
            pytest.fail(f"List strategies subprocess test failed: {e}")
