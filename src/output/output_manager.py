"""Output manager that orchestrates all output generation and formatting."""

from __future__ import annotations
from typing import Dict, List, Any
from datetime import date
from ...core.models import Config
from .generators.schedule import generate_schedule_summary, generate_schedule_metrics
from .formatters.tables import format_schedule_table, format_metrics_table, format_deadline_table
from .file_manager import create_output_directory, save_all_outputs, get_output_summary

def generate_complete_output(schedule: Dict[str, date], config: Config) -> Dict[str, Any]:
    """Generate all output data for a schedule."""
    # Generate metrics
    summary_metrics = generate_schedule_summary(schedule, config)
    detailed_metrics = generate_schedule_metrics(schedule, config)
    
    # Format tables
    schedule_table = format_schedule_table(schedule, config)
    metrics_table = format_metrics_table(summary_metrics)
    deadline_table = format_deadline_table(schedule, config)
    
    return {
        "schedule": schedule,
        "summary_metrics": summary_metrics,
        "detailed_metrics": detailed_metrics,
        "schedule_table": schedule_table,
        "metrics_table": metrics_table,
        "deadline_table": deadline_table
    }

def save_output_to_files(output_data: Dict[str, Any], base_dir: str = "output") -> Dict[str, str]:
    """Save all output data to files and return file paths."""
    # Create output directory
    output_dir = create_output_directory(base_dir)
    
    # Save all files
    saved_files = save_all_outputs(
        schedule=output_data["schedule"],
        schedule_table=output_data["schedule_table"],
        metrics_table=output_data["metrics_table"],
        deadline_table=output_data["deadline_table"],
        metrics=output_data["summary_metrics"],
        output_dir=output_dir
    )
    
    return saved_files

def print_output_summary(output_data: Dict[str, Any]) -> None:
    """Print a summary of the generated output."""
    metrics = output_data["summary_metrics"]
    
    print(f"\n{'='*50}")
    print("SCHEDULE SUMMARY")
    print(f"{'='*50}")
    print(f"Total Submissions: {metrics['total_submissions']}")
    print(f"Schedule Span: {metrics['schedule_span']} days")
    print(f"Start Date: {metrics['start_date']}")
    print(f"End Date: {metrics['end_date']}")
    
    print(f"\n{'='*30}")
    print("QUALITY METRICS")
    print(f"{'='*30}")
    print(f"Penalty Score: ${metrics['penalty_score']:.2f}")
    print(f"Quality Score: {metrics['quality_score']:.3f}")
    print(f"Efficiency Score: {metrics['efficiency_score']:.3f}")
    
    print(f"\n{'='*30}")
    print("COMPLIANCE METRICS")
    print(f"{'='*30}")
    print(f"Deadline Compliance: {metrics['deadline_compliance']:.1f}%")
    print(f"Resource Utilization: {metrics['resource_utilization']:.1%}")

def generate_and_save_output(schedule: Dict[str, date], config: Config, base_dir: str = "output") -> Dict[str, Any]:
    """Generate complete output and save to files."""
    # Generate all output data
    output_data = generate_complete_output(schedule, config)
    
    # Print summary to console
    print_output_summary(output_data)
    
    # Save to files
    saved_files = save_output_to_files(output_data, base_dir)
    
    # Print file summary
    print(f"\n{'='*30}")
    print("FILES SAVED")
    print(f"{'='*30}")
    print(get_output_summary(saved_files))
    
    return output_data 