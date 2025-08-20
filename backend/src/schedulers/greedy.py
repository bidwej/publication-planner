"""Greedy scheduler implementation."""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from schedulers.base import BaseScheduler, SchedulingConfig
from core.dates import is_working_day
from core.models import SchedulerStrategy, SubmissionType, Schedule, Submission
from core.constants import SCHEDULING_CONSTANTS, EFFICIENCY_CONSTANTS


class GreedyScheduler(BaseScheduler):
    """Greedy scheduler that schedules submissions as early as possible based on priority."""
    
    def schedule(self) -> Schedule:
        """Generate a schedule using greedy algorithm.
        
        Returns:
            Schedule object with intervals for all submissions
            
        Raises:
            ValueError: If scheduling fails due to invalid configuration
            RuntimeError: If scheduling algorithm fails to converge
        """
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
    
    def _find_earliest_start(self, submission: Submission, schedule: Schedule, 
                           start_date: date, end_date: date) -> Optional[date]:
        """Find the earliest valid start date for a submission with comprehensive constraint validation.
        
        Args:
            submission: Submission to find start date for
            schedule: Current schedule
            start_date: Earliest allowed start date
            end_date: Latest allowed end date
            
        Returns:
            Earliest valid start date, or None if no valid date found
            
        Raises:
            RuntimeError: If algorithm exceeds maximum iterations
        """
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
            current_date = self._calculate_dependency_start_date(submission, schedule, current_date)
        
        # Check earliest start date constraint for conference submissions
        if submission.conference_id and submission.earliest_start_date:
            current_date = max(current_date, submission.earliest_start_date)
        
        # Check deadline constraint
        if not self._can_meet_deadline_at_date(submission, current_date):
            return None  # Can't meet deadline
        
        # Check resource constraints and all other constraints
        max_concurrent = self.config.max_concurrent_submissions
        max_iterations = getattr(self.config, 'max_iterations', SchedulingConfig.MAX_ITERATIONS)
        iteration_count = 0
        
        while current_date <= end_date and iteration_count < max_iterations:
            iteration_count += 1
            
            # Check resource constraints
            if self._is_resource_available(current_date, schedule, max_concurrent):
                # Check working day constraint only if enabled
                if self._is_working_day_allowed(current_date):
                    # Check all other constraints using comprehensive validation
                    if self.can_schedule(submission, current_date, schedule):
                        return current_date
            
            current_date += timedelta(days=1)
        
        if iteration_count >= max_iterations:
            raise RuntimeError(f"Could not find valid start date for {submission.id} after {max_iterations} iterations")
        
        return None  # Could not find valid start date
    
    def _calculate_dependency_start_date(self, submission: Submission, schedule: Schedule, 
                                       current_date: date) -> date:
        """Calculate the earliest start date based on dependencies.
        
        Args:
            submission: Submission to calculate for
            schedule: Current schedule
            current_date: Current proposed start date
            
        Returns:
            Earliest start date considering dependencies
        """
        if not submission.depends_on:
            return current_date
            
        for dep_id in submission.depends_on:
            if dep_id in schedule:
                dep_interval = schedule.intervals[dep_id]
                current_date = max(current_date, dep_interval.end_date)
        
        return current_date
    
    def _can_meet_deadline_at_date(self, submission: Submission, start_date: date) -> bool:
        """Check if submission can meet deadline at the given start date.
        
        Args:
            submission: Submission to check
            start_date: Proposed start date
            
        Returns:
            True if deadline can be met, False otherwise
        """
        if not submission.conference_id or submission.conference_id not in self.conferences:
            return True  # No deadline to meet
        
        conf = self.conferences[submission.conference_id]
        if submission.kind not in conf.deadlines:
            return True  # No deadline for this type
        
        deadline = conf.deadlines[submission.kind]
        if not deadline:
            return True  # No specific deadline
        
        duration = submission.get_duration_days(self.config)
        latest_start = deadline - timedelta(days=duration)
        return start_date <= latest_start
    
    def _is_resource_available(self, current_date: date, schedule: Schedule, max_concurrent: int) -> bool:
        """Check if resources are available on the given date.
        
        Args:
            current_date: Date to check
            schedule: Current schedule
            max_concurrent: Maximum concurrent submissions allowed
            
        Returns:
            True if resources are available, False otherwise
        """
        active_count = 0
        for scheduled_id, interval in schedule.intervals.items():
            if interval.start_date <= current_date <= interval.end_date:
                active_count += 1
        
        return active_count < max_concurrent
    
    def _is_working_day_allowed(self, current_date: date) -> bool:
        """Check if working day constraints allow scheduling on the given date.
        
        Args:
            current_date: Date to check
            
        Returns:
            True if working day constraints are satisfied, False otherwise
        """
        # Check working day constraint only if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_working_days_only", False)):
            return is_working_day(current_date, self.config.blackout_dates)
        
        return True  # Working day constraints not enabled
