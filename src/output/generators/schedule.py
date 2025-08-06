"""Schedule-specific output generation."""

from __future__ import annotations
from typing import Dict, List
from datetime import date, timedelta, datetime
import os
from core.models import Config, ScheduleSummary, ScheduleMetrics, SubmissionType
from scoring.penalty import calculate_penalty_score
from scoring.quality import calculate_quality_score
from scoring.efficiency import calculate_efficiency_score
from core.constraints import validate_deadline_compliance, validate_resource_constraints
from output.formatters.tables import save_schedule_json, save_table_csv, save_metrics_json
from core.constants import DAYS_PER_MONTH

def create_output_directory(base_dir: str = "output") -> str:
    """Create a timestamped output directory."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(base_dir, f"output_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

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

def generate_schedule_summary(schedule: Dict[str, date], config: Config) -> ScheduleSummary:
    """Generate a comprehensive schedule summary."""
    if not schedule:
        return ScheduleSummary(
            total_submissions=0,
            schedule_span=0,
            start_date=None,
            end_date=None,
            penalty_score=0.0,
            quality_score=0.0,
            efficiency_score=0.0,
            deadline_compliance=100.0,
            resource_utilization=0.0
        )
    
    # Basic schedule metrics
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    schedule_span = (end_date - start_date).days
    
    # Calculate scores
    penalty = calculate_penalty_score(schedule, config)
    quality = calculate_quality_score(schedule, config)
    efficiency = calculate_efficiency_score(schedule, config)
    
    # Calculate compliance
    deadline_validation = validate_deadline_compliance(schedule, config)
    resource_validation = validate_resource_constraints(schedule, config)
    
    return ScheduleSummary(
        total_submissions=len(schedule),
        schedule_span=schedule_span,
        start_date=start_date,
        end_date=end_date,
        penalty_score=penalty.total_penalty,
        quality_score=quality,
        efficiency_score=efficiency,
        deadline_compliance=deadline_validation.compliance_rate,
        resource_utilization=resource_validation.max_observed / resource_validation.max_concurrent if resource_validation.max_concurrent > 0 else 0.0
    )

def generate_schedule_metrics(schedule: Dict[str, date], config: Config) -> ScheduleMetrics:
    """Generate detailed metrics for the schedule."""
    if not schedule:
        return ScheduleMetrics(
            makespan=0,
            avg_utilization=0.0,
            peak_utilization=0,
            total_penalty=0.0,
            compliance_rate=100.0,
            quality_score=0.0
        )
    
    # Calculate makespan
    start_date = min(schedule.values())
    end_date = max(schedule.values())
    makespan = (end_date - start_date).days
    
    # Calculate utilization
    daily_load = {}
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        # Calculate duration
        if sub.kind == SubmissionType.ABSTRACT:
            duration_days = 0
        else:
            duration_days = sub.draft_window_months * DAYS_PER_MONTH if sub.draft_window_months > 0 else config.min_paper_lead_time_days
        
        # Add workload for each day
        for i in range(duration_days + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    avg_utilization = sum(daily_load.values()) / len(daily_load) if daily_load else 0.0
    peak_utilization = max(daily_load.values()) if daily_load else 0
    
    # Calculate penalties and compliance
    penalty = calculate_penalty_score(schedule, config)
    deadline_validation = validate_deadline_compliance(schedule, config)
    quality = calculate_quality_score(schedule, config)
    
    return ScheduleMetrics(
        makespan=makespan,
        avg_utilization=avg_utilization,
        peak_utilization=peak_utilization,
        total_penalty=penalty.total_penalty,
        compliance_rate=deadline_validation.compliance_rate,
        quality_score=quality
    ) 