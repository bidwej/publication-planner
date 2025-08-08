"""Main planner module."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import replace
from datetime import date
from src.core.config import load_config
from src.core.models import Config, SchedulerStrategy, ValidationResult, ScoringResult, ScheduleResult, ScheduleSummary, ScheduleMetrics
from src.core.constants import QUALITY_CONSTANTS
from src.scoring.quality import calculate_quality_score
from src.scoring.penalties import calculate_penalty_score
from src.scoring.efficiency import calculate_efficiency_score, calculate_efficiency_resource, calculate_efficiency_timeline
from src.validation.schedule import validate_schedule_constraints, validate_schedule
from src.scoring.metrics import get_schedule_metrics
from src.schedulers.base import BaseScheduler
# Import scheduler implementations to register them
from src.schedulers.greedy import GreedyScheduler
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.schedulers.lookahead import LookaheadGreedyScheduler
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.schedulers.random import RandomScheduler
from src.schedulers.heuristic import HeuristicScheduler
from src.schedulers.optimal import OptimalScheduler
# Advanced scheduler removed as per requirements

# Import analytics for comprehensive analysis
from src.analytics.analytics import analyze_dependency_graph, get_dependency_chain, get_affected_submissions

# Import monitoring for progress tracking and rescheduling
from src.monitoring.progress import ProgressTracker
from src.monitoring.rescheduler import DynamicRescheduler


class Planner:
    """Main planner for the paper scheduling system."""
        
    def __init__(self, config_path: str):
        """
        Initialize the planner with configuration.
        
        Parameters
        ----------
        config_path : str
            Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
        
        # Initialize monitoring systems
        self.progress_tracker = ProgressTracker(self.config)
        self.rescheduler = DynamicRescheduler(self.config, self.progress_tracker)
    
    def _load_config(self) -> Config:
        """Load and validate the configuration."""
        if not self.config_path.exists():
            print("Configuration file not found: %s", self.config_path)
            print("Using default configuration with sample data")
            return Config.create_default()
        
        try:
            return load_config(str(self.config_path))
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        validation_errors = self.config.validate()
        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            raise ValueError(error_msg)
    
    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters using dataclasses.replace().
        
        Parameters
        ----------
        **kwargs
            Configuration parameters to update
            
        Raises
        ------
        ValueError
            If updated configuration is invalid
        """
        # Use replace() to create a new config instance with updated parameters
        updated_config = replace(self.config, **kwargs)
        
        # Validate the updated configuration
        validation_errors = updated_config.validate()
        if validation_errors:
            error_msg = "Updated configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            raise ValueError(error_msg)
        
        # Update the config if validation passes
        self.config = updated_config
    
    def schedule(self, strategy: SchedulerStrategy = SchedulerStrategy.GREEDY) -> Dict[str, date]:
        """
        Generate a schedule using the specified strategy.
        
        Parameters
        ----------
        strategy : SchedulerStrategy
            The scheduling strategy to use
            
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
            
        Raises
        ------
        RuntimeError
            If schedule generation fails
        """
        try:
            # Create scheduler using the strategy pattern
            scheduler = BaseScheduler.create_scheduler(strategy, self.config)
            
            # Generate schedule
            schedule = scheduler.schedule()
            
            if not schedule:
                print("Warning: No submissions were scheduled")
                return {}
            
            # Validate the generated schedule
            validation_result = validate_schedule_constraints(schedule, self.config)
            if not validation_result["summary"]["overall_valid"]:
                print("Warning: Generated schedule has constraint violations:")
                constraint_result = validation_result["constraints"]
                if "violations" in constraint_result:
                    for violation in constraint_result["violations"]:
                        print("  - %s", violation.get('description', 'Unknown violation'))
            
            return schedule
            
        except ValueError as e:
            raise RuntimeError(f"Schedule generation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during schedule generation: {e}")
    
    def validate_schedule(self, schedule: Dict[str, date]) -> bool:
        """
        Validate a schedule against all constraints.
        
        Parameters
        ----------
        schedule : Dict[str, date]
            The schedule to validate
            
        Returns
        -------
        bool
            True if schedule is valid, False otherwise
        """
        return validate_schedule(schedule, self.config)
    
    def get_schedule_metrics(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a schedule.
        
        Parameters
        ----------
        schedule : Dict[str, date]
            The schedule to analyze
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing various schedule metrics
        """
        return get_schedule_metrics(schedule, self.config)
    
    def get_comprehensive_result(self, schedule: Dict[str, date], strategy: SchedulerStrategy) -> ScheduleResult:
        """
        Get comprehensive result including validation, scoring, and metrics.
        
        Parameters
        ----------
        schedule : Dict[str, date]
            The schedule to analyze
        strategy : SchedulerStrategy
            The strategy used to generate the schedule
            
        Returns
        -------
        ScheduleResult
            Complete result with all metrics and analysis
        """
        # Get validation result
        validation_data = validate_schedule_constraints(schedule, self.config)
        
        # Get analytics
        dependency_analysis = analyze_dependency_graph(self.config)
        
        # Create unified validation result
        validation_result = ValidationResult(
            is_valid=validation_data["summary"]["is_feasible"],
            violations=validation_data.get("constraints", {}).get("violations", []),
            deadline_validation=validation_data.get("deadlines", {}),
            dependency_validation=validation_data.get("dependencies", {}),
            resource_validation=validation_data.get("resources", {}),
            summary=validation_data["summary"].get("summary", "")
        )
        
        # Get scoring results
        penalty_breakdown = calculate_penalty_score(schedule, self.config)
        quality_score = calculate_quality_score(schedule, self.config)
        efficiency_score = calculate_efficiency_score(schedule, self.config)
        efficiency_metrics = calculate_efficiency_resource(schedule, self.config)
        timeline_metrics = calculate_efficiency_timeline(schedule, self.config)
        
        # Create unified scoring result
        scoring_result = ScoringResult(
            penalty_score=penalty_breakdown.total_penalty,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            penalty_breakdown=penalty_breakdown,
            efficiency_metrics=efficiency_metrics,
            timeline_metrics=timeline_metrics,
            overall_score=(quality_score + efficiency_score - penalty_breakdown.total_penalty) / 3
        )
        
        # Calculate schedule summary
        total_submissions = len(schedule)
        if schedule:
            start_date = min(schedule.values())
            end_date = max(schedule.values())
            schedule_span = (end_date - start_date).days
        else:
            start_date = None
            end_date = None
            schedule_span = 0
        
        schedule_summary = ScheduleSummary(
            total_submissions=total_submissions,
            schedule_span=schedule_span,
            start_date=start_date,
            end_date=end_date,
            penalty_score=penalty_breakdown.total_penalty,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            deadline_compliance=QUALITY_CONSTANTS.perfect_compliance_rate if validation_result.is_valid else 0.0,
            resource_utilization=efficiency_metrics.utilization_rate
        )
        
        # Calculate schedule metrics
        schedule_metrics = ScheduleMetrics(
            makespan=schedule_span,
            avg_utilization=efficiency_metrics.avg_utilization,
            peak_utilization=efficiency_metrics.peak_utilization,
            total_penalty=penalty_breakdown.total_penalty,
            compliance_rate=QUALITY_CONSTANTS.perfect_compliance_rate if validation_result.is_valid else 0.0,
            quality_score=quality_score
        )
        
        # Generate tables
        monthly_table = generate_simple_monthly_table(self.config)
        
        # Create schedule result
        return ScheduleResult(
            schedule=schedule,
            summary=schedule_summary,
            metrics=schedule_metrics,
            tables={"monthly": monthly_table},
            validation=validation_result,
            scoring=scoring_result
        )
    
    def generate_monthly_table(self) -> List[Dict[str, Any]]:
        """Generate monthly table for the current configuration."""
        return generate_simple_monthly_table(self.config)
    
    def add_planned_schedule(self, schedule: Dict[str, date]) -> None:
        """Add a planned schedule to track progress."""
        self.progress_tracker.add_planned_schedule(schedule)
    
    def update_progress(self, submission_id: str, actual_start_date: Optional[date] = None,
                       actual_end_date: Optional[date] = None, status: str = "in_progress",
                       notes: Optional[str] = None) -> None:
        """Update progress for a specific submission."""
        self.progress_tracker.update_progress(submission_id, actual_start_date, actual_end_date, status, notes)
    
    def detect_deviations(self) -> List[Dict[str, Any]]:
        """Detect deviations from planned schedule."""
        return self.progress_tracker.detect_deviations()
    
    def generate_progress_report(self) -> Any:
        """Generate a comprehensive progress report."""
        return self.progress_tracker.generate_progress_report()
    
    def reschedule_remaining(self, original_schedule: Dict[str, date]) -> Any:
        """Reschedule remaining submissions based on actual progress."""
        return self.rescheduler.reschedule_remaining(original_schedule)
    
    def get_dependency_chain(self, submission_id: str) -> List[str]:
        """Get the complete dependency chain for a submission."""
        return get_dependency_chain(submission_id, self.config)
    
    def get_affected_submissions(self, submission_id: str) -> List[str]:
        """Get all submissions that would be affected if a submission is delayed."""
        return get_affected_submissions(submission_id, self.config)


def generate_simple_monthly_table(config: Config) -> List[Dict[str, Any]]:
    """Generate a simple monthly table from configuration."""
    # This is a placeholder implementation
    # In a real implementation, this would analyze the schedule and generate monthly statistics
    return [
        {"Month": "2024-01", "Papers": "0", "Deadlines": "0"},
        {"Month": "2024-02", "Papers": "0", "Deadlines": "0"},
        {"Month": "2024-03", "Papers": "0", "Deadlines": "0"}
    ]
