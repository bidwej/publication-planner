"""Enhanced CSV export functionality."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import date
import csv
from pathlib import Path

from src.core.models import Config
from src.analytics.tables import (
    generate_schedule_table,
    generate_metrics_table,
    generate_deadline_table,
    generate_violations_table,
    generate_penalties_table
)
from src.analytics.analytics import (
    analyze_schedule_completeness,
    analyze_schedule_distribution,
    analyze_submission_types,
    analyze_timeline,
    analyze_resources,
    analyze_dependency_graph
)


class CSVExporter:
    """Enhanced CSV export functionality."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def export_schedule_csv(self, schedule: Dict[str, date], filename: str) -> None:
        """Export schedule to CSV format."""
        table_data = generate_schedule_table(schedule, self.config)
        
        if not table_data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = table_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in table_data:
                writer.writerow(row)
    
    def export_metrics_csv(self, schedule: Dict[str, date], filename: str) -> None:
        """Export metrics to CSV format."""
        # Get all analytics
        completeness = analyze_schedule_completeness(schedule, self.config)
        distribution = analyze_schedule_distribution(schedule, self.config)
        submission_types = analyze_submission_types(schedule, self.config)
        timeline = analyze_timeline(schedule, self.config)
        resources = analyze_resources(schedule, self.config)
        
        # Create metrics data
        metrics_data = [
            {
                "Metric": "Total Submissions",
                "Value": completeness.total_count,
                "Category": "Completeness"
            },
            {
                "Metric": "Scheduled Submissions", 
                "Value": completeness.scheduled_count,
                "Category": "Completeness"
            },
            {
                "Metric": "Completion Rate (%)",
                "Value": f"{completeness.completion_rate:.1f}",
                "Category": "Completeness"
            },
            {
                "Metric": "Timeline Duration (days)",
                "Value": timeline.duration_days,
                "Category": "Timeline"
            },
            {
                "Metric": "Peak Daily Load",
                "Value": resources.peak_load,
                "Category": "Resources"
            },
            {
                "Metric": "Average Daily Load",
                "Value": f"{resources.avg_load:.1f}",
                "Category": "Resources"
            }
        ]
        
        # Add submission type metrics
        for sub_type, count in submission_types.type_counts.items():
            metrics_data.append({
                "Metric": f"{sub_type} Count",
                "Value": count,
                "Category": "Submission Types"
            })
        
        # Add monthly distribution
        for month, count in distribution.monthly_distribution.items():
            metrics_data.append({
                "Metric": f"Submissions in {month}",
                "Value": count,
                "Category": "Distribution"
            })
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Metric", "Value", "Category"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in metrics_data:
                writer.writerow(row)
    
    def export_violations_csv(self, violations: List[Dict[str, Any]], filename: str) -> None:
        """Export constraint violations to CSV format."""
        if not violations:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = violations[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for violation in violations:
                writer.writerow(violation)
    
    def export_penalties_csv(self, penalties: List[Dict[str, Any]], filename: str) -> None:
        """Export penalty breakdown to CSV format."""
        if not penalties:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = penalties[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for penalty in penalties:
                writer.writerow(penalty)
    
    def export_dependency_graph_csv(self, filename: str) -> None:
        """Export dependency graph analysis to CSV format."""
        graph_analysis = analyze_dependency_graph(self.config)
        
        # Create dependency data
        dependency_data = []
        for node_id, node in graph_analysis.nodes.items():
            dependency_data.append({
                "Submission ID": node_id,
                "Dependencies": ", ".join(node.dependencies) if node.dependencies else "None",
                "Dependents": ", ".join(node.dependents) if node.dependents else "None",
                "Depth": node.depth,
                "Critical Path": "Yes" if node.critical_path else "No",
                "Is Bottleneck": "Yes" if node_id in graph_analysis.bottlenecks else "No",
                "Is Isolated": "Yes" if node_id in graph_analysis.isolated_nodes else "No"
            })
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Submission ID", "Dependencies", "Dependents", "Depth", 
                         "Critical Path", "Is Bottleneck", "Is Isolated"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in dependency_data:
                writer.writerow(row)
    
    def export_comparison_csv(self, comparison_results: List[Dict[str, Any]], filename: str) -> None:
        """Export strategy comparison results to CSV format."""
        if not comparison_results:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = comparison_results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in comparison_results:
                writer.writerow(result)
    
    def export_all_csv(self, schedule: Dict[str, date], output_dir: str) -> None:
        """Export all CSV files to a directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export schedule
        self.export_schedule_csv(schedule, output_path / "schedule.csv")
        
        # Export metrics
        self.export_metrics_csv(schedule, output_path / "metrics.csv")
        
        # Export dependency graph
        self.export_dependency_graph_csv(output_path / "dependency_graph.csv")
        
        # Export deadlines
        deadline_data = generate_deadline_table(self.config)
        if deadline_data:
            with open(output_path / "deadlines.csv", 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = deadline_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in deadline_data:
                    writer.writerow(row)
    
    def export_custom_csv(self, data: List[Dict[str, Any]], filename: str, 
                         fieldnames: Optional[List[str]] = None) -> None:
        """Export custom data to CSV format."""
        if not data:
            return
        
        if not fieldnames:
            fieldnames = data[0].keys()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
