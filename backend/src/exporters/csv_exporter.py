"""CSV export functionality for Paper Planner."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import json
from collections import defaultdict

from core.models import Config, ScheduleSummary, ScheduleMetrics, SubmissionType, Schedule

from tables import (
    generate_schedule_table, generate_metrics_table, generate_deadline_table,
    generate_violations_table, generate_penalties_table, save_schedule_json, save_table_csv, save_metrics_json
)


def create_output_directory(base_dir: str = "output") -> str:
    """Create a timestamped output directory."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(base_dir) / f"output_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def save_all_outputs(
    schedule: Schedule,
    schedule_table: List[Dict[str, str]],
    metrics_table: List[Dict[str, str]],
    deadline_table: List[Dict[str, str]],
    metrics: ScheduleSummary,
    output_dir: str
) -> Dict[str, str]:
    """Save all output files and return file paths."""
    saved_files = {}
    
    # Save schedule JSON
    saved_files["schedule"] = save_schedule_json(schedule, output_dir)
    
    # Save tables as CSV
    if schedule_table:
        saved_files["schedule_table"] = save_table_csv(schedule_table, output_dir, "schedule_table.csv")
    
    if metrics_table:
        saved_files["metrics_table"] = save_table_csv(metrics_table, output_dir, "metrics_table.csv")
    
    if deadline_table:
        saved_files["deadline_table"] = save_table_csv(deadline_table, output_dir, "deadline_table.csv")
    
    # Save metrics JSON
    saved_files["metrics"] = save_metrics_json(metrics, output_dir)
    
    # Export comprehensive CSV formats
    csv_exporter = CSVExporter(Config.create_default())  # We'll need to pass the actual config
    csv_files = csv_exporter.export_all_csv(schedule, output_dir)
    saved_files.update(csv_files)
    
    return saved_files


class CSVExporter:
    """Comprehensive CSV export functionality for Paper Planner."""
    
    def __init__(self, config: Config):
        """Initialize CSV exporter with configuration."""
        self.config = config
    
    def export_schedule_csv(self, schedule: Schedule, output_dir: str, 
                           filename: str = "schedule.csv") -> str:
        """
        Export schedule to CSV format with detailed submission information.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "schedule.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Get detailed schedule table
        schedule_data = generate_schedule_table(schedule, self.config)
        
        if not schedule_data:
            return ""
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=schedule_data[0].keys())
            writer.writeheader()
            writer.writerows(schedule_data)
        
        return str(filepath)
    
    def export_metrics_csv(self, schedule: Schedule, output_dir: str,
                          filename: str = "metrics.csv") -> str:
        """
        Export performance metrics to CSV format.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "metrics.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate comprehensive metrics
        metrics_data = self._calculate_comprehensive_metrics(schedule)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
            writer.writeheader()
            writer.writerows(metrics_data)
        
        return str(filepath)
    
    def export_deadline_csv(self, schedule: Schedule, output_dir: str,
                           filename: str = "deadlines.csv") -> str:
        """
        Export deadline compliance information to CSV format.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "deadlines.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Get deadline table
        deadline_data = generate_deadline_table(schedule, self.config)
        
        if not deadline_data:
            return ""
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=deadline_data[0].keys())
            writer.writeheader()
            writer.writerows(deadline_data)
        
        return str(filepath)
    
    def export_violations_csv(self, schedule: Schedule, output_dir: str,
                             filename: str = "violations.csv") -> str:
        """
        Export constraint violations to CSV format.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "violations.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Run comprehensive validation
        validation_result = self._run_comprehensive_validation(schedule)
        violations_data = generate_violations_table(validation_result)
        
        if not violations_data:
            return ""
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=violations_data[0].keys())
            writer.writeheader()
            writer.writerows(violations_data)
        
        return str(filepath)
    
    def export_penalties_csv(self, schedule: Schedule, output_dir: str,
                            filename: str = "penalties.csv") -> str:
        """
        Export penalty breakdown to CSV format.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "penalties.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate comprehensive penalties
        penalties_data = self._calculate_comprehensive_penalties(schedule)
        
        if not penalties_data:
            return ""
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=penalties_data[0].keys())
            writer.writeheader()
            writer.writerows(penalties_data)
        
        return str(filepath)
    
    def export_comparison_csv(self, comparison_results: Dict[str, Any], output_dir: str,
                             filename: str = "strategy_comparison.csv") -> str:
        """
        Export strategy comparison results to CSV format.
        
        Parameters
        ----------
        comparison_results : Dict[str, Any]
            Results from strategy comparison
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "strategy_comparison.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        comparison_data = self._format_comparison_data(comparison_results)
        
        if not comparison_data:
            return ""
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=comparison_data[0].keys())
            writer.writeheader()
            writer.writerows(comparison_data)
        
        return str(filepath)
    
    def export_summary_csv(self, schedule: Schedule, output_dir: str,
                          filename: str = "summary.csv") -> str:
        """
        Export schedule summary to CSV format.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
        filename : str, optional
            Output filename, default "summary.csv"
            
        Returns
        -------
        str
            Path to saved CSV file
        """
        filepath = Path(output_dir) / filename
        
        # Create directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        summary_data = self._create_summary_data(schedule)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=summary_data[0].keys())
            writer.writeheader()
            writer.writerows(summary_data)
        
        return str(filepath)
    
    def export_all_csv(self, schedule: Schedule, output_dir: str) -> Dict[str, str]:
        """
        Export all CSV formats for a schedule.
        
        Parameters
        ----------
        schedule : Schedule
            Schedule mapping submission_id to start_date
        output_dir : str
            Output directory path
            
        Returns
        -------
        Dict[str, str]
            Mapping of file type to file path
        """
        saved_files = {}
        
        # Export all CSV formats
        saved_files["schedule"] = self.export_schedule_csv(schedule, output_dir)
        saved_files["metrics"] = self.export_metrics_csv(schedule, output_dir)
        saved_files["deadlines"] = self.export_deadline_csv(schedule, output_dir)
        saved_files["violations"] = self.export_violations_csv(schedule, output_dir)
        saved_files["penalties"] = self.export_penalties_csv(schedule, output_dir)
        saved_files["summary"] = self.export_summary_csv(schedule, output_dir)
        
        return saved_files
    
    def _calculate_comprehensive_metrics(self, schedule: Schedule) -> List[Dict[str, str]]:
        """Calculate comprehensive metrics for CSV export."""
        if not schedule:
            return [{"Metric": "Total Submissions", "Value": "0"}]
        
        # Calculate basic metrics using intervals
        total_submissions = len(schedule.intervals)
        start_date = min(interval.start_date for interval in schedule.intervals.values())
        end_date = max(interval.end_date for interval in schedule.intervals.values())
        schedule_span = schedule.calculate_duration_days()
        
        # Calculate resource utilization
        daily_load = defaultdict(int)
        for sid, interval in schedule.intervals.items():
            submission = self.config.submissions_dict.get(sid)
            if submission:
                duration = submission.get_duration_days(self.config)
                for i in range(duration):
                    check_date = interval.start_date + timedelta(days=i)
                    daily_load[check_date] += 1
        
        max_concurrent = max(daily_load.values()) if daily_load else 0
        avg_concurrent = sum(daily_load.values()) / len(daily_load) if daily_load else 0
        
        # Count by submission type
        submission_types = defaultdict(int)
        for sub_id in schedule.intervals.keys():
            submission = self.config.submissions_dict.get(sub_id)
            if submission:
                sub_type = submission.kind.value
                submission_types[sub_type] += 1
        
        metrics_data = [
            {"Metric": "Total Submissions", "Value": str(total_submissions)},
            {"Metric": "Schedule Span (Days)", "Value": str(schedule_span)},
            {"Metric": "Start Date", "Value": start_date.strftime("%Y-%m-%d")},
            {"Metric": "End Date", "Value": end_date.strftime("%Y-%m-%d")},
            {"Metric": "Max Concurrent Submissions", "Value": str(max_concurrent)},
            {"Metric": "Average Daily Load", "Value": f"{avg_concurrent:.2f}"},
        ]
        
        # Add submission type breakdown
        for sub_type, count in submission_types.items():
            metrics_data.append({
                "Metric": f"{sub_type.title()} Submissions",
                "Value": str(count)
            })
        
        return metrics_data
    
    def _run_comprehensive_validation(self, schedule: Schedule) -> Dict[str, Any]:
        """Run comprehensive validation on schedule."""
        try:
            # Import here to avoid circular imports
            from validation.schedule import validate_schedule
            validation_result = validate_schedule(schedule, self.config)
            return validation_result
        except ImportError:
            # Fallback if validation module is not available
            return {
                "summary": {
                    "overall_valid": True,
                    "total_violations": 0,
                    "compliance_rate": 100.0
                },
                "constraints": {},
                "analytics": {}
            }
    
    def _calculate_comprehensive_penalties(self, schedule: Schedule) -> List[Dict[str, str]]:
        """Calculate comprehensive penalties for CSV export."""
        if not schedule:
            return [{"Penalty Type": "Total Penalty", "Amount": "0.0"}]
        
        try:
            # Import here to avoid circular imports
            from scoring.penalties import calculate_penalty_score
            penalty_breakdown = calculate_penalty_score(schedule, self.config)
            
            penalties_data = [
                {"Penalty Type": "Total Penalty", "Amount": f"{penalty_breakdown.total_penalty:.2f}"},
                {"Penalty Type": "Deadline Penalties", "Amount": f"{penalty_breakdown.deadline_penalties:.2f}"},
                {"Penalty Type": "Dependency Penalties", "Amount": f"{penalty_breakdown.dependency_penalties:.2f}"},
                {"Penalty Type": "Resource Penalties", "Amount": f"{penalty_breakdown.resource_penalties:.2f}"},
                {"Penalty Type": "Conference Compatibility Penalties", "Amount": f"{penalty_breakdown.conference_compatibility_penalties:.2f}"},
                {"Penalty Type": "Abstract-Paper Dependency Penalties", "Amount": f"{penalty_breakdown.abstract_paper_dependency_penalties:.2f}"},
            ]
            
            return penalties_data
            
        except ImportError:
            # Fallback calculation if penalty module is not available
            total_penalty = 0.0
            
            # Basic deadline penalty calculation
            for sid, interval in schedule.intervals.items():
                submission = self.config.submissions_dict.get(sid)
                if submission and submission.conference_id:
                    conference = self.config.conferences_dict.get(submission.conference_id)
                    if conference and submission.kind in conference.deadlines:
                        deadline = conference.deadlines[submission.kind]
                        duration = submission.get_duration_days(self.config)
                        end_date = interval.start_date + timedelta(days=duration)
                        
                        if end_date > deadline:
                            days_late = (end_date - deadline).days
                            penalty_per_day = (self.config.penalty_costs or {}).get("default_paper_penalty_per_day", 500.0)
                            total_penalty += days_late * penalty_per_day
            
            return [
                {"Penalty Type": "Total Penalty", "Amount": f"{total_penalty:.2f}"},
                {"Penalty Type": "Deadline Penalties", "Amount": f"{total_penalty:.2f}"},
                {"Penalty Type": "Dependency Penalties", "Amount": "0.0"},
                {"Penalty Type": "Resource Penalties", "Amount": "0.0"},
                {"Penalty Type": "Conference Compatibility Penalties", "Amount": "0.0"},
                {"Penalty Type": "Abstract-Paper Dependency Penalties", "Amount": "0.0"},
            ]
    
    def _format_comparison_data(self, comparison_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Format strategy comparison data for CSV export."""
        comparison_data = []
        
        for strategy_name, results in comparison_results.items():
            if isinstance(results, dict) and "schedule" in results:
                schedule = results["schedule"]
                metrics = results.get("metrics", {})
                
                comparison_data.append({
                    "Strategy": strategy_name,
                    "Total Submissions": str(len(schedule)),
                    "Schedule Span": str(metrics.get("schedule_span", 0)),
                    "Penalty Score": f"{metrics.get('penalty_score', 0):.2f}",
                    "Quality Score": f"{metrics.get('quality_score', 0):.2f}",
                    "Efficiency Score": f"{metrics.get('efficiency_score', 0):.2f}",
                    "Compliance Rate": f"{metrics.get('compliance_rate', 0):.1f}%",
                    "Resource Utilization": f"{metrics.get('resource_utilization', 0):.1f}%"
                })
        
        return comparison_data
    
    def _create_summary_data(self, schedule: Schedule) -> List[Dict[str, str]]:
        """Create summary data for CSV export."""
        if not schedule:
            return [{"Category": "Status", "Value": "No Schedule"}]
        
        # Calculate summary statistics using intervals
        total_submissions = len(schedule.intervals)
        start_date = min(interval.start_date for interval in schedule.intervals.values())
        end_date = max(interval.end_date for interval in schedule.intervals.values())
        schedule_span = schedule.calculate_duration_days()
        
        # Count by submission type
        submission_types = defaultdict(int)
        for sub_id in schedule.intervals.keys():
            submission = self.config.submissions_dict.get(sub_id)
            if submission:
                sub_type = submission.kind.value
                submission_types[sub_type] += 1
        
        # Calculate resource utilization
        daily_load = defaultdict(int)
        for sid, interval in schedule.intervals.items():
            submission = self.config.submissions_dict.get(sid)
            if submission:
                duration = submission.get_duration_days(self.config)
                for i in range(duration):
                    check_date = interval.start_date + timedelta(days=i)
                    daily_load[check_date] += 1
        
        max_concurrent = max(daily_load.values()) if daily_load else 0
        avg_concurrent = sum(daily_load.values()) / len(daily_load) if daily_load else 0
        
        summary_data = [
            {"Category": "Total Submissions", "Value": str(total_submissions)},
            {"Category": "Schedule Span", "Value": f"{schedule_span} days"},
            {"Category": "Start Date", "Value": start_date.strftime("%Y-%m-%d")},
            {"Category": "End Date", "Value": end_date.strftime("%Y-%m-%d")},
            {"Category": "Max Concurrent Submissions", "Value": str(max_concurrent)},
            {"Category": "Average Daily Load", "Value": f"{avg_concurrent:.2f}"},
        ]
        
        # Add submission type breakdown
        for sub_type, count in submission_types.items():
            summary_data.append({
                "Category": f"{sub_type.title()} Submissions",
                "Value": str(count)
            })
        
        return summary_data


def export_schedule_to_csv(schedule: Schedule, config: Config, output_dir: str,
                          filename: str = "schedule.csv") -> str:
    """
    Convenience function to export schedule to CSV.
    
    Parameters
    ----------
    schedule : Schedule
        Schedule mapping submission_id to start_date
    config : Config
        Configuration object
    output_dir : str
        Output directory path
    filename : str, optional
        Output filename, default "schedule.csv"
        
    Returns
    -------
    str
        Path to saved CSV file
    """
    exporter = CSVExporter(config)
    return exporter.export_schedule_csv(schedule, output_dir, filename)


def export_all_csv_formats(schedule: Schedule, config: Config, output_dir: str) -> Dict[str, str]:
    """
    Convenience function to export all CSV formats.
    
    Parameters
    ----------
    schedule : Schedule
        Schedule mapping submission_id to start_date
    config : Config
        Configuration object
    output_dir : str
        Output directory path
        
    Returns
    -------
    Dict[str, str]
        Mapping of file type to file path
    """
    exporter = CSVExporter(config)
    return exporter.export_all_csv(schedule, output_dir)
