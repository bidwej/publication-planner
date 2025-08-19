"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from src.schedulers.base import BaseScheduler
from src.core.dates import is_working_day
from src.core.models import SchedulerStrategy, SubmissionType, Schedule, Submission
from src.core.constants import SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS


class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    def schedule(self) -> Schedule:
        """Generate a schedule using greedy algorithm."""
        
        # Get what we need from base
        topo = self.get_dependency_order()
        start_date, end_date = self.get_scheduling_window()
        
        # Initialize empty Schedule object
        schedule = Schedule()
        
        # Schedule each submission in dependency/priority order
        for submission_id in topo:
            if submission_id in schedule:
                continue
                
            submission = self.submissions[submission_id]
            
            # Find earliest valid start date
            proposed_start_date = self._find_earliest_valid_start(submission, schedule)
            
            if proposed_start_date:
                # Add interval to schedule
                schedule.add_interval(submission_id, proposed_start_date, duration_days=submission.get_duration_days(self.config))
            else:
                # If we can't schedule this submission, skip it
                continue
        
        # Print scheduling summary
        self._print_scheduling_summary(schedule)
        
        return schedule
    
    def _find_earliest_valid_start(self, submission: Submission, schedule: Schedule) -> Optional[date]:
        """Find the earliest valid start date for a submission with comprehensive constraint validation."""
        
        # If submission doesn't have a conference assigned, try to assign one
        if submission.conference_id is None and hasattr(submission, 'preferred_conferences') and submission.preferred_conferences:
            self._assign_best_conference(submission)
        
        # For work items (no conference), start with earliest start date if available
        # For conference submissions, start with today
        if submission.conference_id is None and submission.earliest_start_date:
            # Work items should be scheduled at their intended start date
            current_date = submission.earliest_start_date
        else:
            # Conference submissions start with today
            current_date = date.today()
        
        # Check dependencies
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in schedule:
                    dep_interval = schedule.intervals[dep_id]
                    current_date = max(current_date, dep_interval.end_date)
        
        # Check earliest start date constraint for conference submissions
        if submission.conference_id and submission.earliest_start_date:
            current_date = max(current_date, submission.earliest_start_date)
        
        # Check deadline constraint
        if submission.conference_id:
            conf = self.conferences.get(submission.conference_id)
            if conf and submission.kind in conf.deadlines:
                deadline = conf.deadlines[submission.kind]
                duration = submission.get_duration_days(self.config)
                latest_start = deadline - timedelta(days=duration)
                if current_date > latest_start:
                    return None  # Can't meet deadline
        
        # Check resource constraints and all other constraints
        max_concurrent = self.config.max_concurrent_submissions
        max_iterations = EFFICIENCY_CONSTANTS.max_algorithm_iterations  # Safety limit to prevent infinite loops
        iteration_count = 0
        
        while current_date <= date.today() + timedelta(days=365) and iteration_count < max_iterations:  # Reasonable limit
            iteration_count += 1
            
            # Count active submissions on this date
            active_count = 0
            for scheduled_id, interval in schedule.intervals.items():
                if interval.start_date <= current_date <= interval.end_date:
                    active_count += 1
            
            # Check resource constraint
            if active_count >= max_concurrent:
                current_date += timedelta(days=1)
                continue
            
            # Check working day constraint only if enabled
            if (self.config.scheduling_options and 
                self.config.scheduling_options.get("enable_working_days_only", False) and
                not is_working_day(current_date, self.config.blackout_dates)):
                current_date += timedelta(days=1)
                continue
            
            # Check all other constraints using comprehensive validation
            if self.validate_constraints(submission, current_date, schedule):
                return current_date
            
            current_date += timedelta(days=1)
        
        if iteration_count >= max_iterations:
            print(f"Warning: Could not find valid start date for {submission.id} after {max_iterations} iterations")
        
        return None  # Could not find valid start date 
    
    def _assign_best_conference(self, submission: Submission) -> None:
        """Assign the best available conference to a submission."""
        preferred_conferences = self._get_preferred_conferences(submission)
        if not preferred_conferences:
            return
            
        # Try to find the best conference for this submission
        for conf_name in preferred_conferences:
            conf = self._find_conference_by_name(conf_name)
            if not conf:
                continue
                
            if self._try_assign_conference(submission, conf):
                return
    
    def _get_preferred_conferences(self, submission: Submission) -> List[str]:
        """Get list of preferred conferences for a submission."""
        if hasattr(submission, 'preferred_conferences') and submission.preferred_conferences:
            return submission.preferred_conferences
        
        # Open to any opportunity if no specific preferences
        if (submission.preferred_kinds is None or 
            (submission.preferred_workflow and submission.preferred_workflow.value == "all_types")):
            return [conf.name for conf in self.conferences.values() if conf.deadlines]
        
        # Use specific preferred_kinds
        preferred_conferences = []
        for conf in self.conferences.values():
            if any(ctype in conf.deadlines for ctype in (submission.preferred_kinds or [submission.kind])):
                preferred_conferences.append(conf.name)
        return preferred_conferences
    
    def _find_conference_by_name(self, conf_name: str):
        """Find conference by name."""
        for conf in self.conferences.values():
            if conf.name == conf_name:
                return conf
        return None
    
    def _try_assign_conference(self, submission: Submission, conf) -> bool:
        """Try to assign a submission to a specific conference. Returns True if successful."""
        
        submission_types_to_try = self._get_submission_types_to_try(submission)
        
        for submission_type in submission_types_to_try:
            if submission_type not in conf.deadlines:
                continue
                
            if not self._can_meet_deadline(submission, conf, submission_type):
                continue
                
            if not self._check_conference_compatibility_for_type(conf, submission_type):
                continue
                
            # Handle special case: papers at conferences requiring abstracts
            if (submission_type == SubmissionType.PAPER and 
                conf.requires_abstract_before_paper() and 
                SubmissionType.ABSTRACT in conf.deadlines):
                submission.conference_id = conf.id
                submission.preferred_kinds = [SubmissionType.ABSTRACT]
                return True
            
            # Regular assignment
            submission.conference_id = conf.id
            if submission.preferred_kinds is None:
                submission.preferred_kinds = [submission_type]
            return True
        
        return False
    
    def _get_submission_types_to_try(self, submission: Submission) -> List[SubmissionType]:
        """Get list of submission types to try in priority order."""
        if submission.preferred_kinds is not None:
            return submission.preferred_kinds
        
        if (submission.preferred_workflow and 
            submission.preferred_workflow.value == "all_types"):
            return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
        
        # Default priority order
        return [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
    
    def _can_meet_deadline(self, submission: Submission, conf, submission_type: SubmissionType) -> bool:
        """Check if submission can meet the deadline for a specific submission type."""
        duration = submission.get_duration_days(self.config)
        latest_start = conf.deadlines[submission_type] - timedelta(days=duration)
        return latest_start >= date.today()

    def _check_conference_compatibility_for_type(self, conference, submission_type: SubmissionType) -> bool:
        """Check if a submission is compatible with a conference for a specific submission type."""
        return submission_type in conference.deadlines
    

    
    def _print_scheduling_summary(self, schedule: Schedule) -> None:
        """Print summary of scheduling results."""
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            print(f"Note: Could not schedule {len(missing)} submissions: {missing}")
        print(f"Successfully scheduled {len(schedule)} out of {len(self.submissions)} submissions")
