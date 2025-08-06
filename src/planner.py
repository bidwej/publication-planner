"""Main planner module for the Endoscope AI project."""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import date


from core.config import load_config
from core.models import Config, SchedulerStrategy
from schedulers.base import BaseScheduler
from core.constraints import validate_schedule_comprehensive
from output.console import print_schedule_summary, print_metrics_summary
from output.reports import generate_schedule_report
from output.tables import generate_monthly_table, generate_simple_monthly_table
from output.formatters.tables import format_schedule_table, format_deadline_table
from output.plots import plot_schedule, plot_utilization_chart, plot_deadline_compliance


def generate_and_save_output(schedule: Dict[str, date], config: Config, output_dir: str = "test_output") -> None:
    """
    Generate and save all output files for a schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Mapping of submission_id to start_date
    config : Config
        Configuration object
    output_dir : str
        Directory to save output files
    """
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate reports
    report = generate_schedule_report(schedule, config)
    
    # Save report to JSON
    report_path = os.path.join(output_dir, f"schedule_report_{timestamp}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Generate and save tables
    try:
        schedule_table_data = format_schedule_table(schedule, config)
        table_path = os.path.join(output_dir, f"schedule_table_{timestamp}.txt")
        with open(table_path, 'w', encoding='utf-8') as f:
            for row in schedule_table_data:
                f.write(" | ".join(f"{k}: {v}" for k, v in row.items()) + "\n")
    except Exception as e:
        print(f"Warning: Could not generate schedule table: {e}")
    
    try:
        deadline_table_data = format_deadline_table(schedule, config)
        deadline_path = os.path.join(output_dir, f"deadline_table_{timestamp}.txt")
        with open(deadline_path, 'w', encoding='utf-8') as f:
            for row in deadline_table_data:
                f.write(" | ".join(f"{k}: {v}" for k, v in row.items()) + "\n")
    except Exception as e:
        print(f"Warning: Could not generate deadline table: {e}")
    
    # Generate and save plots
    try:
        plot_path = os.path.join(output_dir, f"schedule_gantt_{timestamp}.png")
        plot_schedule(schedule, config.submissions, save_path=plot_path)
    except Exception as e:
        print(f"Warning: Could not generate schedule plot: {e}")
    
    try:
        util_path = os.path.join(output_dir, f"utilization_{timestamp}.png")
        plot_utilization_chart(schedule, config, save_path=util_path)
    except Exception as e:
        print(f"Warning: Could not generate utilization plot: {e}")
    
    try:
        deadline_plot_path = os.path.join(output_dir, f"deadline_compliance_{timestamp}.png")
        plot_deadline_compliance(schedule, config, save_path=deadline_plot_path)
    except Exception as e:
        print(f"Warning: Could not generate deadline compliance plot: {e}")
    
    print(f"Output files saved to: {output_dir}")
    print(f"Report: {report_path}")


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
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            return load_config(str(self.config_path))
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def _validate_config(self) -> None:
        """Validate the loaded configuration."""
        if not self.config.submissions:
            raise ValueError("No submissions found in configuration")
        
        if not self.config.conferences:
            raise ValueError("No conferences found in configuration")
        
        # Validate that all submissions have valid conference references
        conference_ids = {conf.id for conf in self.config.conferences}
        for submission in self.config.submissions:
            if submission.conference_id and submission.conference_id not in conference_ids:
                raise ValueError(f"Submission {submission.id} references unknown conference {submission.conference_id}")
    
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
        from scoring.penalty import calculate_penalty_score
        from scoring.quality import calculate_quality_score
        from scoring.efficiency import calculate_efficiency_score
        
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
    
    def generate_monthly_table(self) -> List[Dict[str, Any]]:
        """Generate monthly table for the current configuration."""
        return generate_simple_monthly_table(self.config)
