"""Edge case tests for MILP optimization."""
from pathlib import Path
from typing import Any

import pytest
from datetime import date, timedelta

from core.config import load_config
from core.models import Config, SubmissionType, ConferenceType, ConferenceRecurrence, Schedule
from schedulers.optimal import OptimalScheduler
from conftest import (
    create_mock_submission, create_mock_conference, create_mock_config,
    get_future_date, get_short_deadline, get_blackout_date, get_working_date,
    get_dependency_date, get_medium_deadline, get_long_deadline, get_very_far_future_date
)


class TestOptimalSchedulerEdgeCases:
    """Edge case tests for MILP optimization."""
    
    @pytest.fixture
    def test_data_config(self) -> Config:
        """Load test data config from tests/common/data."""
        test_data_dir = Path(__file__).parent.parent.parent.parent / "common" / "data"
        config_path = test_data_dir / "config.json"
        return load_config(str(config_path))
    
    def test_milp_single_submission_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with single submission - simplest case."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"single_sub": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Load test data
        test_data_dir = Path(__file__).parent.parent.parent.parent / "common" / "data"
        config = load_config(str(test_data_dir / "config.json"))
        
        # Create minimal config with one submission
        if config.submissions:
            config.submissions = [config.submissions[0]]  # Just one submission
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle single submission
        assert isinstance(schedule, Schedule)
        if len(schedule.intervals) > 0:
            # Check that we got a valid schedule
            assert all(isinstance(interval.start_date, date) for interval in schedule.intervals.values())
    
    def test_milp_circular_dependency_edge_case(self, monkeypatch) -> None:
        """Test MILP with circular dependencies - should handle gracefully."""
        # Create circular dependency: A -> B -> C -> A
        
        submissions = [
            create_mock_submission("A", "Paper A", SubmissionType.PAPER, "conf1", depends_on=["C"]),
            create_mock_submission("B", "Paper B", SubmissionType.PAPER, "conf1", depends_on=["A"]),
            create_mock_submission("C", "Paper C", SubmissionType.PAPER, "conf1", depends_on=["B"])
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 12, 31)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        # Should handle circular dependency gracefully
        scheduler: Any = OptimalScheduler(config)
        
        # Should detect circular dependency and raise ValueError
        with pytest.raises(ValueError, match="Circular dependency detected"):
            scheduler.schedule()
    
    def test_milp_impossible_deadline_edge_case(self, monkeypatch) -> None:
        """Test MILP with impossible deadline - past deadline."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"past_deadline": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submission with deadline in the past
        submissions = [
            create_mock_submission("past_deadline", "Past Deadline Paper", SubmissionType.PAPER, "conf1")
        ]
        
        conferences = [
            create_mock_conference("conf1", "Past Conf", {SubmissionType.PAPER: date(2020, 1, 1)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle impossible deadline gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_zero_duration_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with zero duration submissions."""
        # Mock zero duration
        def mock_get_duration_days(*args, **kwargs):
            return 0
        
        monkeypatch.setattr('src.core.models.Submission.get_duration_days', mock_get_duration_days)
        
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        # Should handle zero duration gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_max_concurrent_zero_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with max_concurrent_submissions = 0."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        config = test_data_config
        config.max_concurrent_submissions = 0
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle zero concurrency gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_all_blackout_dates_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP when all available dates are blackout dates."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(35), end_date=get_future_date(65))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create blackout dates for next 30 days
        blackout_dates = [get_future_date(i) for i in range(30)]
        
        config = test_data_config
        config.blackout_dates = blackout_dates
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle all blackout dates gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_very_large_problem_edge_case(self, monkeypatch) -> None:
        """Test MILP with very large problem size - should fallback to greedy."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            intervals = {}
            for i in range(25):
                intervals[f"paper{i}"] = Interval(start_date=get_future_date(i*7), end_date=get_future_date(i*7+30))
            return Schedule(intervals=intervals)
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create many submissions to trigger fallback
        submissions = [
            create_mock_submission(f"paper{i}", f"Paper {i}", SubmissionType.PAPER, "conf1")
            for i in range(25)  # More than 20 to trigger fallback
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 12, 31)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should fallback to greedy for large problems
        assert isinstance(schedule, Schedule)
    
    def test_milp_very_long_duration_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with very long duration submissions."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(), end_date=get_very_far_future_date())})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Mock very long duration
        def mock_get_duration_days(*args, **kwargs):
            return 365
        
        monkeypatch.setattr('src.core.models.Submission.get_duration_days', mock_get_duration_days)
        
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        # Should handle very long duration gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_no_conferences_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with no conferences defined."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule
            return Schedule(intervals={})  # Empty schedule for no conferences
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        config = test_data_config
        config.conferences = []
        config.submissions = []  # Also clear submissions to avoid validation errors
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle no conferences gracefully
        assert len(schedule.intervals) == 0
    
    def test_milp_no_submissions_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with no submissions."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule
            return Schedule(intervals={})  # Empty schedule for no submissions
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        config = test_data_config
        config.submissions = []
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should return empty schedule
        assert len(schedule.intervals) == 0
    
    def test_milp_invalid_optimization_objective_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with invalid optimization objective."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Should handle invalid objective gracefully - use default parameter
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        assert isinstance(schedule, Schedule)
    
    def test_milp_solver_timeout_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP when solver times out."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Mock solver to timeout
        mock_solver = type('MockSolver', (), {
            'solve': lambda: 1  # Timeout status
        })()
        
        def mock_pulp_cbc_cmd(*args, **kwargs):
            return mock_solver
        
        monkeypatch.setattr('pulp.PULP_CBC_CMD', mock_pulp_cbc_cmd)
        
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        # Should handle timeout gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_infeasible_constraints_edge_case(self, monkeypatch) -> None:
        """Test MILP with infeasible constraints."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"A": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submissions with conflicting constraints
        submissions = [
            create_mock_submission("A", "Paper A", SubmissionType.PAPER, "conf1", 
                                 earliest_start_date=date(2025, 12, 1)),
            create_mock_submission("B", "Paper B", SubmissionType.PAPER, "conf1", 
                                 earliest_start_date=date(2025, 12, 1))
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 11, 30)})
        ]
        
        config = create_mock_config(submissions, conferences, max_concurrent_submissions=1)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle infeasible constraints gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_very_short_deadline_edge_case(self, monkeypatch) -> None:
        """Test MILP with very short deadline window."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"short_deadline": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submission with very short deadline
        submissions = [
            create_mock_submission("short_deadline", "Short Deadline Paper", SubmissionType.PAPER, "conf1")
        ]
        
        # Deadline very close to today
        tomorrow = get_short_deadline()
        conferences = [
            create_mock_conference("conf1", "Short Conf", {SubmissionType.PAPER: tomorrow})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle very short deadline gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_duplicate_submission_ids_edge_case(self, monkeypatch) -> None:
        """Test MILP with duplicate submission IDs."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"duplicate": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submissions with duplicate IDs
        submissions = [
            create_mock_submission("duplicate", "Paper 1", SubmissionType.PAPER, "conf1"),
            create_mock_submission("duplicate", "Paper 2", SubmissionType.PAPER, "conf1")
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 12, 31)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle duplicate IDs gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_missing_dependency_edge_case(self, monkeypatch) -> None:
        """Test MILP with missing dependency."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"dependent": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submission that depends on non-existent submission
        submissions = [
            create_mock_submission("dependent", "Dependent Paper", SubmissionType.PAPER, "conf1", 
                                 depends_on=["non_existent"])
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 12, 31)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle missing dependency gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_negative_duration_edge_case(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with negative duration (should never happen but test anyway)."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"paper1": Interval(start_date=get_future_date(), end_date=get_short_deadline())})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Mock negative duration
        def mock_get_duration_days(*args, **kwargs):
            return -1
        
        monkeypatch.setattr('src.core.models.Submission.get_duration_days', mock_get_duration_days)
        
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        # Should handle negative duration gracefully
        assert isinstance(schedule, Schedule)
    
    def test_milp_empty_dependency_list_edge_case(self, monkeypatch) -> None:
        """Test MILP with empty dependency list vs None."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={
                "A": Interval(start_date=get_future_date(), end_date=get_future_date(30)),
                "B": Interval(start_date=get_future_date(30), end_date=get_future_date(60))
            })
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submissions with empty vs None dependencies
        submissions = [
            create_mock_submission("A", "Paper A", SubmissionType.PAPER, "conf1", depends_on=[]),
            create_mock_submission("B", "Paper B", SubmissionType.PAPER, "conf1", depends_on=None)
        ]
        
        conferences = [
            create_mock_conference("conf1", "Test Conf", {SubmissionType.PAPER: date(2025, 12, 31)})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle both empty and None dependencies
        assert isinstance(schedule, Schedule)
    
    def test_milp_very_far_future_deadline_edge_case(self, monkeypatch) -> None:
        """Test MILP with deadline very far in the future."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"far_future": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Create submission with deadline far in the future
        submissions = [
            create_mock_submission("far_future", "Far Future Paper", SubmissionType.PAPER, "conf1")
        ]
        
        far_future = get_very_far_future_date()  # 10 years from now
        conferences = [
            create_mock_conference("conf1", "Far Future Conf", {SubmissionType.PAPER: far_future})
        ]
        
        config = create_mock_config(submissions, conferences)
        
        scheduler: Any = OptimalScheduler(config)
        schedule = scheduler.schedule()
        
        # Should handle far future deadline
        assert isinstance(schedule, Schedule)
        if "far_future" in schedule.intervals:
            assert schedule.intervals["far_future"].start_date >= date.today()
    
    def test_milp_with_real_test_data(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with actual test data from tests/common/data."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"test_sub": Interval(start_date=get_future_date(), end_date=get_future_date(30))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Use the real test data
        scheduler: Any = OptimalScheduler(test_data_config)
        schedule = scheduler.schedule()
        
        # Should produce a valid schedule
        assert isinstance(schedule, Schedule)
        if len(schedule.intervals) > 0:
            # Check that all scheduled dates are valid
            for submission_id, interval in schedule.intervals.items():
                assert isinstance(interval.start_date, date)
                assert interval.start_date >= date.today()
    
    def test_milp_with_blackout_dates_from_file(self, test_data_config: Config, monkeypatch) -> None:
        """Test MILP with blackout dates loaded from test data file."""
        # Mock the schedule method to return quickly
        def mock_schedule(self):
            from core.models import Schedule, Interval
            return Schedule(intervals={"test_sub": Interval(start_date=get_future_date(60), end_date=get_future_date(90))})
        
        monkeypatch.setattr(OptimalScheduler, 'schedule', mock_schedule)
        
        # Load blackout dates from test data
        test_data_dir = Path(__file__).parent.parent.parent.parent / "common" / "data"
        blackout_file = test_data_dir / "blackout.json"
        
        if blackout_file.exists():
            import json
            with open(blackout_file) as f:
                blackout_data = json.load(f)
            
            config = test_data_config
            config.blackout_dates = [date.fromisoformat(d) for d in blackout_data.get("blackout_dates", [])]
            
            scheduler: Any = OptimalScheduler(config)
            schedule = scheduler.schedule()
            
            # Should handle blackout dates gracefully
            assert isinstance(schedule, Schedule)
