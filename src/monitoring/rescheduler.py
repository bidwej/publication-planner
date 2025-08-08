"""Dynamic rescheduling based on actual progress."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from dataclasses import dataclass

from src.core.models import Config, Submission
from src.schedulers.base import BaseScheduler
from src.schedulers.greedy import GreedyScheduler
from .progress import ProgressTracker, ProgressEntry


@dataclass
class RescheduleResult:
    """Result of a rescheduling operation."""
    original_schedule: Dict[str, date]
    new_schedule: Dict[str, date]
    rescheduled_submissions: List[str]
    unchanged_submissions: List[str]
    removed_submissions: List[str]
    added_submissions: List[str]
    summary: str


class DynamicRescheduler:
    """Dynamically reschedule remaining submissions based on actual progress."""
    
    def __init__(self, config: Config, progress_tracker: ProgressTracker):
        self.config = config
        self.progress_tracker = progress_tracker
        self.scheduler = GreedyScheduler(config)  # Default to greedy scheduler
    
    def reschedule_remaining(self, original_schedule: Dict[str, date]) -> RescheduleResult:
        """Reschedule remaining submissions based on actual progress."""
        # Get completed and in-progress submissions
        completed_submissions = []
        in_progress_submissions = []
        remaining_submissions = []
        
        for submission_id, planned_start in original_schedule.items():
            entry = self.progress_tracker.progress_entries.get(submission_id)
            if entry:
                if entry.status == "completed":
                    completed_submissions.append(submission_id)
                elif entry.status == "in_progress":
                    in_progress_submissions.append(submission_id)
                else:
                    remaining_submissions.append(submission_id)
            else:
                remaining_submissions.append(submission_id)
        
        # Create new config with only remaining submissions
        remaining_config = self._create_remaining_config(remaining_submissions)
        
        if not remaining_config.submissions:
            # No remaining submissions to reschedule
            return RescheduleResult(
                original_schedule=original_schedule,
                new_schedule=original_schedule,
                rescheduled_submissions=[],
                unchanged_submissions=list(original_schedule.keys()),
                removed_submissions=[],
                added_submissions=[],
                summary="No remaining submissions to reschedule"
            )
        
        # Create new scheduler with remaining submissions
        remaining_scheduler = GreedyScheduler(remaining_config)
        
        # Generate new schedule for remaining submissions
        new_remaining_schedule = remaining_scheduler.schedule()
        
        # Combine completed, in-progress, and new schedules
        new_schedule = {}
        
        # Add completed submissions (keep original dates)
        for submission_id in completed_submissions:
            new_schedule[submission_id] = original_schedule[submission_id]
        
        # Add in-progress submissions (keep original dates)
        for submission_id in in_progress_submissions:
            new_schedule[submission_id] = original_schedule[submission_id]
        
        # Add rescheduled submissions
        for submission_id, new_start_date in new_remaining_schedule.items():
            new_schedule[submission_id] = new_start_date
        
        # Determine what changed
        rescheduled_submissions = list(new_remaining_schedule.keys())
        unchanged_submissions = completed_submissions + in_progress_submissions
        removed_submissions = [sid for sid in original_schedule.keys() 
                             if sid not in new_schedule]
        added_submissions = [sid for sid in new_schedule.keys() 
                           if sid not in original_schedule]
        
        summary = f"Rescheduled {len(rescheduled_submissions)} submissions, " \
                 f"{len(unchanged_submissions)} unchanged, " \
                 f"{len(removed_submissions)} removed, " \
                 f"{len(added_submissions)} added"
        
        return RescheduleResult(
            original_schedule=original_schedule,
            new_schedule=new_schedule,
            rescheduled_submissions=rescheduled_submissions,
            unchanged_submissions=unchanged_submissions,
            removed_submissions=removed_submissions,
            added_submissions=added_submissions,
            summary=summary
        )
    
    def _create_remaining_config(self, remaining_submission_ids: List[str]) -> Config:
        """Create a new config with only the remaining submissions."""
        remaining_submissions = []
        remaining_conferences = []
        
        # Get remaining submissions
        for submission_id in remaining_submission_ids:
            submission = self.config.submissions_dict.get(submission_id)
            if submission:
                remaining_submissions.append(submission)
        
        # Get conferences needed by remaining submissions
        conference_ids = set()
        for submission in remaining_submissions:
            if submission.conference_id:
                conference_ids.add(submission.conference_id)
        
        for conference in self.config.conferences:
            if conference.id in conference_ids:
                remaining_conferences.append(conference)
        
        # Create new config with remaining data
        return Config(
            submissions=remaining_submissions,
            conferences=remaining_conferences,
            min_abstract_lead_time_days=self.config.min_abstract_lead_time_days,
            min_paper_lead_time_days=self.config.min_paper_lead_time_days,
            max_concurrent_submissions=self.config.max_concurrent_submissions,
            default_paper_lead_time_months=self.config.default_paper_lead_time_months,
            penalty_costs=self.config.penalty_costs,
            priority_weights=self.config.priority_weights,
            scheduling_options=self.config.scheduling_options,
            blackout_dates=self.config.blackout_dates,
            data_files=self.config.data_files
        )
    
    def update_dependencies(self, completed_submissions: List[str]) -> None:
        """Update dependency chains based on completed submissions."""
        # Remove completed submissions from dependency lists
        for submission in self.config.submissions:
            if submission.depends_on:
                # Remove completed submissions from dependencies
                submission.depends_on = [
                    dep_id for dep_id in submission.depends_on 
                    if dep_id not in completed_submissions
                ]
    
    def detect_cascade_effects(self, delayed_submissions: List[str]) -> List[Dict[str, Any]]:
        """Detect cascade effects of delayed submissions."""
        cascade_effects = []
        
        for delayed_submission_id in delayed_submissions:
            # Find submissions that depend on the delayed submission
            dependent_submissions = []
            for submission in self.config.submissions:
                if (submission.depends_on and 
                    delayed_submission_id in submission.depends_on):
                    dependent_submissions.append(submission.id)
            
            if dependent_submissions:
                cascade_effects.append({
                    "delayed_submission": delayed_submission_id,
                    "affected_submissions": dependent_submissions,
                    "severity": "high" if len(dependent_submissions) > 2 else "medium"
                })
        
        return cascade_effects
