"""Progress tracking for actual vs. planned schedules."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from dataclasses import dataclass

from core.models import Config, Submission


@dataclass
class ProgressEntry:
    """A single progress entry for a submission."""
    submission_id: str
    planned_start_date: date
    planned_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: str = "planned"  # planned, in_progress, completed, delayed
    notes: Optional[str] = None


@dataclass
class ProgressReport:
    """A comprehensive progress report."""
    total_submissions: int
    completed_submissions: int
    in_progress_submissions: int
    delayed_submissions: int
    on_time_submissions: int
    completion_rate: float
    on_time_rate: float
    average_delay_days: float
    entries: List[ProgressEntry]
    summary: str


class ProgressTracker:
    """Track actual progress vs. planned schedules."""
    
    def __init__(self, config: Config):
        self.config = config
        self.progress_entries: Dict[str, ProgressEntry] = {}
    
    def add_planned_schedule(self, schedule: Dict[str, date]) -> None:
        """Add a planned schedule to track."""
        for submission_id, start_date in schedule.items():
            submission = self.config.submissions_dict.get(submission_id)
            if submission:
                duration_days = submission.get_duration_days(self.config)
                end_date = start_date + timedelta(days=duration_days)
                
                self.progress_entries[submission_id] = ProgressEntry(
                    submission_id=submission_id,
                    planned_start_date=start_date,
                    planned_end_date=end_date,
                    status="planned"
                )
    
    def update_progress(self, submission_id: str, actual_start_date: Optional[date] = None,
                       actual_end_date: Optional[date] = None, status: str = "in_progress",
                       notes: Optional[str] = None) -> None:
        """Update progress for a specific submission."""
        if submission_id in self.progress_entries:
            entry = self.progress_entries[submission_id]
            if actual_start_date:
                entry.actual_start_date = actual_start_date
            if actual_end_date:
                entry.actual_end_date = actual_end_date
            entry.status = status
            if notes:
                entry.notes = notes
    
    def detect_deviations(self) -> List[Dict[str, Any]]:
        """Detect deviations from planned schedule."""
        deviations = []
        today = date.today()
        
        for submission_id, entry in self.progress_entries.items():
            deviation = None
            
            # Check if submission is behind schedule
            if entry.status == "planned" and today > entry.planned_start_date:
                days_delayed = (today - entry.planned_start_date).days
                deviation = {
                    "submission_id": submission_id,
                    "type": "start_delay",
                    "days_delayed": days_delayed,
                    "severity": "high" if days_delayed > 30 else "medium"
                }
            elif entry.status == "in_progress" and entry.actual_start_date:
                if entry.actual_start_date > entry.planned_start_date:
                    days_delayed = (entry.actual_start_date - entry.planned_start_date).days
                    deviation = {
                        "submission_id": submission_id,
                        "type": "start_delay",
                        "days_delayed": days_delayed,
                        "severity": "high" if days_delayed > 30 else "medium"
                    }
            
            if deviation:
                deviations.append(deviation)
        
        return deviations
    
    def generate_progress_report(self) -> ProgressReport:
        """Generate a comprehensive progress report."""
        total = len(self.progress_entries)
        completed = sum(1 for entry in self.progress_entries.values() if entry.status == "completed")
        in_progress = sum(1 for entry in self.progress_entries.values() if entry.status == "in_progress")
        delayed = sum(1 for entry in self.progress_entries.values() if entry.status == "delayed")
        on_time = sum(1 for entry in self.progress_entries.values() 
                     if entry.actual_start_date and entry.actual_start_date <= entry.planned_start_date)
        
        completion_rate = (completed / total * 100) if total > 0 else 0.0
        on_time_rate = (on_time / total * 100) if total > 0 else 0.0
        
        # Calculate average delay
        delays = []
        for entry in self.progress_entries.values():
            if entry.actual_start_date and entry.actual_start_date > entry.planned_start_date:
                delay = (entry.actual_start_date - entry.planned_start_date).days
                delays.append(delay)
        
        average_delay = sum(delays) / len(delays) if delays else 0.0
        
        summary = f"Progress: {completed}/{total} completed ({completion_rate:.1f}%), {on_time}/{total} on time ({on_time_rate:.1f}%)"
        
        return ProgressReport(
            total_submissions=total,
            completed_submissions=completed,
            in_progress_submissions=in_progress,
            delayed_submissions=delayed,
            on_time_submissions=on_time,
            completion_rate=completion_rate,
            on_time_rate=on_time_rate,
            average_delay_days=average_delay,
            entries=list(self.progress_entries.values()),
            summary=summary
        )
    
    def get_remaining_schedule(self) -> Dict[str, date]:
        """Get the remaining schedule for incomplete submissions."""
        remaining = {}
        for submission_id, entry in self.progress_entries.items():
            if entry.status in ["planned", "delayed"]:
                # Use actual start date if available, otherwise planned
                start_date = entry.actual_start_date or entry.planned_start_date
                remaining[submission_id] = start_date
        
        return remaining
