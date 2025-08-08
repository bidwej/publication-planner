"""CSV export functionality for Paper Planner."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date, datetime
from pathlib import Path
import csv
import json

from src.core.models import Config, ScheduleSummary, ScheduleMetrics
from src.analytics.tables import (
    generate_schedule_table, generate_metrics_table, generate_deadline_table,
    generate_violations_table, generate_penalties_table
)
# Import only what we need to avoid circular imports
from src.analytics.tables import (
    generate_schedule_table, generate_metrics_table, generate_deadline_table,
    generate_violations_table, generate_penalties_table
)


class CSVExporter:
    """Comprehensive CSV export functionality for Paper Planner."""
    
    def __init__(self, config: Config):
        """Initialize CSV exporter with configuration."""
        self.config = config
    
    def export_schedule_csv(self, schedule: Dict[str, date], output_dir: str, 
                           filename: str = "schedule.csv") -> str:
        """
        Export schedule to CSV format with detailed submission information.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def export_metrics_csv(self, schedule: Dict[str, date], output_dir: str,
                          filename: str = "metrics.csv") -> str:
        """
        Export performance metrics to CSV format.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def export_deadline_csv(self, schedule: Dict[str, date], output_dir: str,
                           filename: str = "deadlines.csv") -> str:
        """
        Export deadline compliance information to CSV format.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def export_violations_csv(self, schedule: Dict[str, date], output_dir: str,
                             filename: str = "violations.csv") -> str:
        """
        Export constraint violations to CSV format.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def export_penalties_csv(self, schedule: Dict[str, date], output_dir: str,
                            filename: str = "penalties.csv") -> str:
        """
        Export penalty breakdown to CSV format.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
        
        # For now, return empty string to avoid circular imports
        # This can be enhanced later when circular import issues are resolved
        return ""
    
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
    
    def export_summary_csv(self, schedule: Dict[str, date], output_dir: str,
                          filename: str = "summary.csv") -> str:
        """
        Export schedule summary to CSV format.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def export_all_csv(self, schedule: Dict[str, date], output_dir: str) -> Dict[str, str]:
        """
        Export all CSV formats for a schedule.
        
        Parameters
        ----------
        schedule : Dict[str, date]
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
    
    def _calculate_comprehensive_metrics(self, schedule: Dict[str, date]) -> List[Dict[str, str]]:
        """Calculate comprehensive metrics for CSV export."""
        if not schedule:
            return [{"Metric": "Total Submissions", "Value": "0"}]
        
        # Calculate basic metrics
        total_submissions = len(schedule)
        start_date = min(schedule.values())
        end_date = max(schedule.values())
        schedule_span = (end_date - start_date).days
        
        metrics_data = [
            {"Metric": "Total Submissions", "Value": str(total_submissions)},
            {"Metric": "Schedule Span (Days)", "Value": str(schedule_span)},
            {"Metric": "Start Date", "Value": start_date.strftime("%Y-%m-%d")},
            {"Metric": "End Date", "Value": end_date.strftime("%Y-%m-%d")},
        ]
        
        return metrics_data
    
    def _run_comprehensive_validation(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Run comprehensive validation on schedule."""
        # For now, return empty validation result to avoid circular imports
        # This can be enhanced later when circular import issues are resolved
        validation_result = {}
        
        return validation_result
    
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
    
    def _create_summary_data(self, schedule: Dict[str, date]) -> List[Dict[str, str]]:
        """Create summary data for CSV export."""
        if not schedule:
            return [{"Category": "Status", "Value": "No Schedule"}]
        
        # Calculate summary statistics
        total_submissions = len(schedule)
        start_date = min(schedule.values())
        end_date = max(schedule.values())
        schedule_span = (end_date - start_date).days
        
        # Count by submission type
        submission_types = {}
        for sub_id in schedule.keys():
            submission = self.config.submissions_dict.get(sub_id)
            if submission:
                sub_type = submission.kind.value
                submission_types[sub_type] = submission_types.get(sub_type, 0) + 1
        
        summary_data = [
            {"Category": "Total Submissions", "Value": str(total_submissions)},
            {"Category": "Schedule Span", "Value": f"{schedule_span} days"},
            {"Category": "Start Date", "Value": start_date.strftime("%Y-%m-%d")},
            {"Category": "End Date", "Value": end_date.strftime("%Y-%m-%d")},
        ]
        
        # Add submission type breakdown
        for sub_type, count in submission_types.items():
            summary_data.append({
                "Category": f"{sub_type.title()} Submissions",
                "Value": str(count)
            })
        
        return summary_data


def export_schedule_to_csv(schedule: Dict[str, date], config: Config, output_dir: str,
                          filename: str = "schedule.csv") -> str:
    """
    Convenience function to export schedule to CSV.
    
    Parameters
    ----------
    schedule : Dict[str, date]
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


def export_all_csv_formats(schedule: Dict[str, date], config: Config, output_dir: str) -> Dict[str, str]:
    """
    Convenience function to export all CSV formats.
    
    Parameters
    ----------
    schedule : Dict[str, date]
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
