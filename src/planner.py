"""Main planner module for the Endoscope AI project."""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import date

from core.config import load_config
from core.models import Config, SchedulerStrategy, ValidationResult, ScoringResult, ScheduleResult, ScheduleSummary, ScheduleMetrics
from core.constants import PERFECT_COMPLIANCE_RATE
from schedulers.base import BaseScheduler
# Import all schedulers to register them
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler
from schedulers.random import RandomScheduler
from schedulers.heuristic import HeuristicScheduler
from schedulers.optimal import OptimalScheduler
from core.constraints import validate_schedule_comprehensive
from scoring.penalty import calculate_penalty_score
from scoring.quality import calculate_quality_score
from scoring.efficiency import calculate_efficiency_score, calculate_efficiency_resource, calculate_efficiency_timeline
from output.tables import generate_simple_monthly_table


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
    
    def _load_config(self) -> Config:
        """Load and validate the configuration."""
        if not self.config_path.exists():
            print(f"Configuration file not found: {self.config_path}")
            print("Using default configuration with sample data...")
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
                raise RuntimeError("Failed to generate schedule - no submissions scheduled")
            
            # Validate the generated schedule
            validation_result = validate_schedule_comprehensive(schedule, self.config)
            if not validation_result["summary"]["is_feasible"]:
                print("Warning: Generated schedule has constraint violations:")
                constraint_result = validation_result["constraints"]
                if "violations" in constraint_result:
                    for violation in constraint_result["violations"]:
                        print(f"  - {violation.get('description', 'Unknown violation')}")
            
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
        validation_result = validate_schedule_comprehensive(schedule, self.config)
        return validation_result["summary"]["is_feasible"]
    
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
        # Calculate scores
        penalty_breakdown = calculate_penalty_score(schedule, self.config)
        quality_score = calculate_quality_score(schedule, self.config)
        efficiency_score = calculate_efficiency_score(schedule, self.config)
        
        # Calculate basic metrics
        total_submissions = len(schedule)
        if schedule:
            start_date = min(schedule.values())
            end_date = max(schedule.values())
            duration_days = (end_date - start_date).days
        else:
            duration_days = 0
        
        return {
            "total_submissions": total_submissions,
            "duration_days": duration_days,
            "penalty_score": penalty_breakdown.total_penalty,
            "quality_score": quality_score,
            "efficiency_score": efficiency_score,
            "penalty_breakdown": {
                "deadline_penalties": penalty_breakdown.deadline_penalties,
                "dependency_penalties": penalty_breakdown.dependency_penalties,
                "resource_penalties": penalty_breakdown.resource_penalties
            }
        }
    
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
        validation_data = validate_schedule_comprehensive(schedule, self.config)
        
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
            deadline_compliance=PERFECT_COMPLIANCE_RATE if validation_result.is_valid else 0.0,
            resource_utilization=efficiency_metrics.utilization_rate
        )
        
        # Calculate schedule metrics
        schedule_metrics = ScheduleMetrics(
            makespan=schedule_span,
            avg_utilization=efficiency_metrics.avg_utilization,
            peak_utilization=efficiency_metrics.peak_utilization,
            total_penalty=penalty_breakdown.total_penalty,
            compliance_rate=PERFECT_COMPLIANCE_RATE if validation_result.is_valid else 0.0,
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
