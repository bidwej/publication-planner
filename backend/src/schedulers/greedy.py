"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from schedulers.base import BaseScheduler
from core.dates import is_working_day
from core.models import SchedulerStrategy, SubmissionType, Schedule, Submission
from core.constants import SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS


class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    # ===== PUBLIC INTERFACE METHODS =====
    
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
            proposed_start_date = self._find_earliest_start(submission, schedule, start_date, end_date)
            
            if proposed_start_date:
                # Add interval to schedule
                schedule.add_interval(submission_id, proposed_start_date, duration_days=submission.get_duration_days(self.config))
            else:
                # If we can't schedule this submission, skip it
                continue
        
        # Print scheduling summary
        self.print_scheduling_summary(schedule)
        
        return schedule
    
    # ===== GREEDY-SPECIFIC METHODS =====
    
    def _find_earliest_start(self, submission: Submission, schedule: Schedule, 
                           start_date: date, end_date: date) -> Optional[date]:
        """Find the earliest valid start date for a submission with comprehensive constraint validation."""
        # If submission doesn't have a conference assigned, try to assign one
        if submission.conference_id is None:
            self.assign_conference(submission)
        
        # For work items (no conference), start with earliest start date if available
        # For conference submissions, start with a reasonable date that allows meeting deadlines
        if submission.conference_id is None and submission.earliest_start_date:
            # Work items should be scheduled at their intended start date
            current_date = submission.earliest_start_date
        else:
            # Conference submissions should start early enough to meet deadlines
            # Use the start_date parameter passed to this method
            current_date = start_date
        
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
        
        while current_date <= end_date and iteration_count < max_iterations:  # Use actual scheduling window
            iteration_count += 1
            
            # Count active submissions on this date
            active_count = 0
            for scheduled_id, interval in schedule.intervals.items():  # pylint: disable=unused-variable
                if interval.start_date <= current_date <= interval.end_date:
                    active_count += 1
            
            # Check if we can schedule at this date
            if active_count < max_concurrent:
                # Check working days constraint
                if (self.config.scheduling_options and 
                    self.config.scheduling_options.get("enable_working_days_only", False)):
                    if not is_working_day(current_date, self.config.blackout_dates):
                        current_date += timedelta(days=1)
                        continue
                
                # Check all other constraints using base class method
                if self.validate_constraints(submission, current_date, schedule):
                    return current_date
            
            current_date += timedelta(days=1)
        
        return None  # Couldn't find a valid start date
