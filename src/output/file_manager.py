"""File management utilities for output operations."""

from __future__ import annotations
import os
import json
import csv
from typing import Dict, List, Any
from datetime import datetime
from core.models import ScheduleSummary

def create_output_directory(base_dir: str = "output") -> str:
    """Create a timestamped output directory."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(base_dir, f"output_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_schedule_json(schedule: Dict[str, str], output_dir: str, filename: str = "schedule.json") -> str:
    """Save schedule as JSON file."""
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(schedule, f, default=str, indent=2)
    return filepath

def save_table_csv(table_data: List[Dict[str, str]], output_dir: str, filename: str) -> str:
    """Save table data as CSV file."""
    if not table_data:
        return ""
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=table_data[0].keys())
        writer.writeheader()
        writer.writerows(table_data)
    return filepath

def save_metrics_json(metrics: ScheduleSummary, output_dir: str, filename: str = "metrics.json") -> str:
    """Save metrics as JSON file."""
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(metrics, f, default=str, indent=2)
    return filepath

def save_all_outputs(
    schedule: Dict[str, str],
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
    
    return saved_files

def get_output_summary(saved_files: Dict[str, str]) -> str:
    """Generate a summary of saved output files."""
    if not saved_files:
        return "No files were saved."
    
    summary = "Output files saved:\n"
    for file_type, filepath in saved_files.items():
        if filepath:
            filename = os.path.basename(filepath)
            summary += f"  - {filename}\n"
    
    return summary 