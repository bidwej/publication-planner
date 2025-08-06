"""Generate planner that orchestrates all output generation and formatting."""

from __future__ import annotations
from typing import Dict
from datetime import date, timedelta
from core.models import Config, CompleteOutput
from .generators.schedule import generate_schedule_summary, generate_schedule_metrics
from .formatters.tables import format_schedule_table, format_metrics_table, format_deadline_table
from .file_manager import create_output_directory, save_all_outputs, get_output_summary


class GeneratePlanner:
    """Planner for generating complete output from schedules."""
    
    def __init__(self, config: Config):
        """Initialize the generate planner with configuration."""
        self.config = config
    
    def generate_complete_output(self, schedule: Dict[str, date]) -> CompleteOutput:
        """Generate all output data for a schedule."""
        # Generate metrics
        summary_metrics = generate_schedule_summary(schedule, self.config)
        detailed_metrics = generate_schedule_metrics(schedule, self.config)
        
        # Format tables
        schedule_table = format_schedule_table(schedule, self.config)
        metrics_table = format_metrics_table(summary_metrics)
        deadline_table = format_deadline_table(schedule, self.config)
        
        return CompleteOutput(
            schedule=schedule,
            summary_metrics=summary_metrics,
            detailed_metrics=detailed_metrics,
            schedule_table=schedule_table,
            metrics_table=metrics_table,
            deadline_table=deadline_table
        )
    
    def save_output_to_files(self, output_data: CompleteOutput, base_dir: str = "output") -> Dict[str, str]:
        """Save all output data to files and return file paths."""
        # Create output directory
        output_dir = create_output_directory(base_dir)
        
        # Save all files
        saved_files = save_all_outputs(
            schedule=output_data.schedule,
            schedule_table=output_data.schedule_table,
            metrics_table=output_data.metrics_table,
            deadline_table=output_data.deadline_table,
            metrics=output_data.summary_metrics,
            output_dir=output_dir
        )
        
        return saved_files
    
    def print_output_summary(self, output_data: CompleteOutput) -> None:
        """Print a summary of the generated output."""
        metrics = output_data.summary_metrics
        
        print(f"\n{'='*50}")
        print("SCHEDULE SUMMARY")
        print(f"{'='*50}")
        print(f"Total Submissions: {metrics.total_submissions}")
        print(f"Schedule Span: {metrics.schedule_span} days")
        print(f"Start Date: {metrics.start_date}")
        print(f"End Date: {metrics.end_date}")
        
        print(f"\n{'='*30}")
        print("QUALITY METRICS")
        print(f"{'='*30}")
        print(f"Penalty Score: ${metrics.penalty_score:.2f}")
        print(f"Quality Score: {metrics.quality_score:.3f}")
        print(f"Efficiency Score: {metrics.efficiency_score:.3f}")
        
        print(f"\n{'='*30}")
        print("COMPLIANCE METRICS")
        print(f"{'='*30}")
        print(f"Deadline Compliance: {metrics.deadline_compliance:.1f}%")
        print(f"Resource Utilization: {metrics.resource_utilization:.1%}")
    
    def generate_and_save_output(self, schedule: Dict[str, date], base_dir: str = "output") -> CompleteOutput:
        """Generate complete output and save to files."""
        # Generate all output data
        output_data = self.generate_complete_output(schedule)
        
        # Print summary to console
        self.print_output_summary(output_data)
        
        # Save to files
        saved_files = self.save_output_to_files(output_data, base_dir)
        
        # Print file summary
        print(f"\n{'='*30}")
        print("FILES SAVED")
        print(f"{'='*30}")
        print(get_output_summary(saved_files))
        
        return output_data
    
    def validate_schedule(self, schedule: Dict[str, date]) -> bool:
        """Validate that the schedule is complete and valid."""
        if not schedule:
            return False
        
        # Check that all submissions in config are scheduled
        config_submission_ids = {sub.id for sub in self.config.submissions}
        scheduled_ids = set(schedule.keys())
        
        # All submissions should be scheduled
        return scheduled_ids.issuperset(config_submission_ids)
    
    def get_schedule_statistics(self, schedule: Dict[str, date]) -> Dict[str, any]:
        """Get comprehensive statistics about the schedule."""
        if not schedule:
            return {
                "total_submissions": 0,
                "scheduled_submissions": 0,
                "completion_rate": 0.0,
                "schedule_span_days": 0,
                "avg_daily_load": 0.0,
                "peak_daily_load": 0
            }
        
        # Calculate basic statistics
        total_submissions = len(self.config.submissions)
        scheduled_submissions = len(schedule)
        completion_rate = (scheduled_submissions / total_submissions * 100) if total_submissions > 0 else 0.0
        
        # Calculate schedule span
        if schedule:
            start_date = min(schedule.values())
            end_date = max(schedule.values())
            schedule_span_days = (end_date - start_date).days
        else:
            schedule_span_days = 0
        
        # Calculate daily load (simplified)
        daily_load = {}
        for submission_id, start_date in schedule.items():
            submission = next((s for s in self.config.submissions if s.id == submission_id), None)
            if submission:
                duration_days = submission.draft_window_months * 30 if submission.draft_window_months else 60
                for i in range(duration_days):
                    day = start_date + timedelta(days=i)
                    daily_load[day] = daily_load.get(day, 0) + 1
        
        avg_daily_load = sum(daily_load.values()) / len(daily_load) if daily_load else 0.0
        peak_daily_load = max(daily_load.values()) if daily_load else 0
        
        return {
            "total_submissions": total_submissions,
            "scheduled_submissions": scheduled_submissions,
            "completion_rate": completion_rate,
            "schedule_span_days": schedule_span_days,
            "avg_daily_load": avg_daily_load,
            "peak_daily_load": peak_daily_load
        }


# Backward compatibility functions
def generate_complete_output(schedule: Dict[str, date], config: Config) -> CompleteOutput:
    """Generate all output data for a schedule (backward compatibility)."""
    planner = GeneratePlanner(config)
    return planner.generate_complete_output(schedule)


def save_output_to_files(output_data: CompleteOutput, base_dir: str = "output") -> Dict[str, str]:
    """Save all output data to files and return file paths (backward compatibility)."""
    # Create a temporary planner to use the method
    planner = GeneratePlanner(output_data.summary_metrics.config if hasattr(output_data.summary_metrics, 'config') else None)
    return planner.save_output_to_files(output_data, base_dir)


def print_output_summary(output_data: CompleteOutput) -> None:
    """Print a summary of the generated output (backward compatibility)."""
    # Create a temporary planner to use the method
    planner = GeneratePlanner(output_data.summary_metrics.config if hasattr(output_data.summary_metrics, 'config') else None)
    planner.print_output_summary(output_data)


def generate_and_save_output(schedule: Dict[str, date], config: Config, base_dir: str = "output") -> CompleteOutput:
    """Generate complete output and save to files (backward compatibility)."""
    planner = GeneratePlanner(config)
    return planner.generate_and_save_output(schedule, base_dir)
