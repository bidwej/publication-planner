"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional
from datetime import date, timedelta
from src.core.models import (
    Config, Submission, SubmissionType, SchedulerStrategy, Conference
)
from src.core.constants import SCHEDULING_CONSTANTS
from src.core.dates import is_working_day


class BaseScheduler(ABC):
    """Abstract base scheduler that defines the interface and shared utilities."""
    
    # Strategy registry
    _strategy_registry: Dict[SchedulerStrategy, Type['BaseScheduler']] = {}
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
    
    @classmethod
    def register_strategy(cls, strategy: SchedulerStrategy):
        """Decorator to register a scheduler class with a strategy."""
        def decorator(scheduler_class: Type['BaseScheduler']):
            cls._strategy_registry[strategy] = scheduler_class
            return scheduler_class
        return decorator
    
    @classmethod
    def create_scheduler(cls, strategy: SchedulerStrategy, config: Config) -> 'BaseScheduler':
        """Create a scheduler instance for the given strategy."""
        if strategy not in cls._strategy_registry:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        scheduler_class = cls._strategy_registry[strategy]
        return scheduler_class(config)
    
    @abstractmethod
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule for all submissions.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
    
    # Shared utility methods
    def _topological_order(self) -> List[str]:
        """Get submissions in topological order based on dependencies."""
        return list(self.submissions.keys())
    
    def _deps_satisfied(self, sub: Submission, schedule: Dict[str, date], current: date) -> bool:
        """Check if all dependencies are satisfied."""
        from src.validation.submission import _validate_dependencies_satisfied
        return _validate_dependencies_satisfied(sub, schedule, self.submissions, self.config, current)
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate end date for a submission."""
        lead_time = self.config.min_paper_lead_time_days
        if sub.kind.value == "ABSTRACT":
            lead_time = self.config.min_abstract_lead_time_days
        return start + timedelta(days=lead_time)
    
    def _meets_deadline(self, submission: Submission, start_date: date) -> bool:
        """Check if starting on this date meets the deadline."""
        # Create a temporary schedule with just this submission
        temp_schedule = {submission.id: start_date}
        from src.validation.deadline import validate_deadline_constraints
        result = validate_deadline_constraints(temp_schedule, self.config)
        return result.is_valid
    
    # VALIDATION METHODS - Call comprehensive validation from all validation files
    # These methods provide fast boolean validation during scheduling by calling
    # the comprehensive validation functions from all validation modules
    
    def _validate_all_constraints(self, sub: Submission, start: date, schedule: Dict[str, date]) -> bool:
        """Validate all constraints for a submission at a given start date."""
        # Use the centralized submission validation - it already calls all necessary validations
        from src.validation.submission import validate_submission_constraints
        
        # This single call handles deadline, dependency, and venue validation
        # No need to duplicate validation calls
        return validate_submission_constraints(sub, start, schedule, self.config)
    
    def _run_common_scheduling_setup(self) -> tuple[Dict[str, date], List[str], date, date]:
        """
        Common setup for all schedulers.
        
        Returns
        -------
        tuple[Dict[str, date], List[str], date, date]
            (schedule, topological_order, start_date, end_date)
        """
        # Validate venue compatibility
        from src.validation.venue import _validate_venue_compatibility
        _validate_venue_compatibility(self.submissions, self.conferences)
        
        # Get submissions in topological order
        topo = self._topological_order()
        
        # Get scheduling window
        start_date, end_date = self._get_scheduling_window()
        
        # Initialize schedule
        schedule: Dict[str, date] = {}
        
        return schedule, topo, start_date, end_date
    
    def _apply_early_abstract_scheduling(self, schedule: Dict[str, date]) -> None:
        """Apply early abstract scheduling if enabled in config."""
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get(
                "abstract_advance_days", 
                SCHEDULING_CONSTANTS.abstract_advance_days
            )
            self._schedule_early_abstracts(schedule, abstract_advance)
    
    def _get_ready_submissions(self, topo: List[str], schedule: Dict[str, date], current_date: date) -> List[str]:
        """
        Get list of submissions ready to be scheduled at the current date.
        
        Parameters
        ----------
        topo : List[str]
            Submissions in topological order
        schedule : Dict[str, date]
            Current schedule
        current_date : date
            Current date being considered
            
        Returns
        -------
        List[str]
            List of submission IDs ready to be scheduled
        """
        ready = []
        for submission_id in topo:
            if submission_id in schedule:
                continue
            
            submission = self.submissions[submission_id]
            
            # Check dependencies
            if not self._deps_satisfied(submission, schedule, current_date):
                continue
            
            # Check earliest start date
            earliest_start = self._calculate_earliest_start_date(submission)
            if current_date < earliest_start:
                continue
            
            ready.append(submission_id)
        
        return ready
    
    def _update_active_submissions(self, active: List[str], schedule: Dict[str, date], current_date: date) -> List[str]:
        """
        Update list of active submissions by removing finished ones.
        
        Parameters
        ----------
        active : List[str]
            Current list of active submission IDs
        schedule : Dict[str, date]
            Current schedule
        current_date : date
            Current date being considered
            
        Returns
        -------
        List[str]
            Updated list of active submission IDs
        """
        return [
            submission_id for submission_id in active
            if self._get_end_date(schedule[submission_id], self.submissions[submission_id]) > current_date
        ]
    
    def _schedule_submissions_up_to_limit(self, ready: List[str], schedule: Dict[str, date], 
                                        active: List[str], current_date: date) -> int:
        """
        Schedule submissions up to the concurrency limit.
        
        Parameters
        ----------
        ready : List[str]
            List of submission IDs ready to be scheduled
        schedule : Dict[str, date]
            Current schedule
        active : List[str]
            Current list of active submission IDs
        current_date : date
            Current date being considered
            
        Returns
        -------
        int
            Number of submissions scheduled in this round
        """
        scheduled_count = 0
        
        for submission_id in ready:
            if len(active) >= self.config.max_concurrent_submissions:
                break
            
            submission = self.submissions[submission_id]
            
            # IMPORTANT: Try to assign conference BEFORE validation if not assigned
            if submission.conference_id is None and hasattr(submission, 'candidate_conferences') and submission.candidate_conferences:
                self._assign_best_conference(submission)
            
            # Check deadline constraint
            if not self._meets_deadline(submission, current_date):
                continue
            
            # Check all constraints using comprehensive validation
            if not self._validate_all_constraints(submission, current_date, schedule):
                continue
            
            # Schedule the submission
            schedule[submission_id] = current_date
            active.append(submission_id)
            scheduled_count += 1
        
        return scheduled_count
    
    def _print_scheduling_summary(self, schedule: Dict[str, date]) -> None:
        """Print summary of scheduling results."""
        if len(schedule) != len(self.submissions):
            missing = [submission_id for submission_id in self.submissions if submission_id not in schedule]
            print(f"Note: Could not schedule {len(missing)} submissions: {missing}")
            print(f"Successfully scheduled {len(schedule)} out of {len(self.submissions)} submissions")
    
    def _advance_date_if_needed(self, current_date: date) -> date:
        """Advance date if it's not a working day."""
        while not is_working_day(current_date, self.config.blackout_dates):
            current_date += timedelta(days=1)
        return current_date
    
    def _get_base_priority(self, submission: Submission) -> float:
        """Get base priority for a submission based on config weights."""
        weights = self.config.priority_weights or {}
        
        if submission.kind.value == "PAPER":
            weight_key = "engineering_paper" if submission.engineering else "medical_paper"
            return weights.get(weight_key, 1.0)
        elif submission.kind.value == "ABSTRACT":
            return weights.get("abstract", 0.5)
        elif submission.kind.value == "POSTER":
            return weights.get("poster", 0.8)
        else:
            return weights.get("mod", 1.5)
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight."""
        def get_priority(submission_id: str) -> float:
            submission = self.submissions[submission_id]
            return self._get_base_priority(submission)
        
        return sorted(ready, key=get_priority, reverse=True)
    

    
    def _assign_conferences(self, schedule: Dict[str, date]) -> Dict[str, date]:
        """Assign conferences to submissions that don't have them."""
        for sub_id in schedule.keys():
            submission = self.submissions[sub_id]
            
            # Skip if already has conference
            if submission.conference_id:
                continue
                
            # Assign conference using the new logic
            self._assign_best_conference(submission)
        
        return schedule
    
    def _assign_best_conference(self, submission: Submission) -> None:
        """Assign the best available conference to a submission."""
        candidate_conferences = []
        
        if hasattr(submission, 'candidate_conferences') and submission.candidate_conferences:
            # Use specific candidate conferences
            candidate_conferences = submission.candidate_conferences
        else:
            # None or empty candidate_conferences means try all appropriate conferences
            # If candidate_kinds is None, try all conferences that accept any submission type
            if submission.candidate_kinds is None:
                # Open to any opportunity - find conferences that accept any submission type
                for conf in self.conferences.values():
                    # Accept conference if it has any deadline (abstract, paper, poster)
                    if conf.deadlines:
                        candidate_conferences.append(conf.name)
            else:
                # Use specific candidate_kinds
                for conf in self.conferences.values():
                    # Check if any candidate_kinds are accepted by this conference
                    candidate_types = submission.candidate_kinds if submission.candidate_kinds else [submission.kind]
                    if any(ctype in conf.deadlines for ctype in candidate_types):
                        candidate_conferences.append(conf.name)
        
        if not candidate_conferences:
            return
            
        # Try to find the best conference for this submission
        for conf_name in candidate_conferences:
            # Find conference by name
            conf = None
            for c in self.conferences.values():
                if c.name == conf_name:
                    conf = c
                    break
                    
            if conf:
                # Determine what submission type to use
                if submission.candidate_kinds is not None:
                    # Use specified candidate_kinds in priority order
                    submission_types_to_try = submission.candidate_kinds
                else:
                    # Open to any opportunity - try in order of preference: poster, abstract, paper
                    submission_types_to_try = [SubmissionType.POSTER, SubmissionType.ABSTRACT, SubmissionType.PAPER]
                
                # Try each submission type in order
                for submission_type_to_check in submission_types_to_try:
                    if submission_type_to_check in conf.deadlines:
                        duration = submission.get_duration_days(self.config)
                        latest_start = conf.deadlines[submission_type_to_check] - timedelta(days=duration)
                        
                        # Check if we can meet the deadline
                        if latest_start >= date.today():
                            # Check if this conference is compatible
                            if self._check_conference_compatibility_for_type(conf, submission_type_to_check):
                                # Special handling for papers at conferences requiring abstracts
                                if (submission_type_to_check == SubmissionType.PAPER and 
                                    conf.requires_abstract_before_paper()):
                                    # For now, assign as abstract instead of paper
                                    # This preserves the business requirement that abstracts come before papers
                                    if SubmissionType.ABSTRACT in conf.deadlines:
                                        submission.conference_id = conf.id
                                        submission.candidate_kinds = [SubmissionType.ABSTRACT]  # Submit as abstract first
                                        return
                                else:
                                    submission.conference_id = conf.id
                                    # Update candidate_kinds to reflect the chosen type
                                    if submission.candidate_kinds is None:
                                        submission.candidate_kinds = [submission_type_to_check]
                                    return
    
    def _check_conference_compatibility_for_type(self, conference: 'Conference', submission_type: SubmissionType) -> bool:
        """Check if a submission is compatible with a conference for a specific submission type."""
        from src.core.models import ConferenceType
        
        # Check if conference accepts the submission type
        if submission_type not in conference.deadlines:
            return False
        
        # Conference accepts this submission type, so it's compatible
        return True
    
    def _check_conference_compatibility(self, submission: Submission, conference: 'Conference') -> bool:
        """Check if a submission is compatible with a conference based on the compatibility matrix."""
        from src.core.models import ConferenceType
        
        # Check if conference accepts any of the candidate submission types
        candidate_types = submission.candidate_kinds if submission.candidate_kinds else [submission.kind]
        
        # Try each candidate type in priority order
        for submission_type in candidate_types:
            if submission_type in conference.deadlines:
                # Found a compatible type - conference accepts this submission type
                submission_type_to_check = submission_type
                break
        else:
            # No compatible type found
            return False
        
        # Check if conference is abstract-only (no paper deadline)
        if (SubmissionType.ABSTRACT in conference.deadlines and 
            SubmissionType.PAPER not in conference.deadlines):
            # Abstract-only conference - papers cannot be assigned
            if submission.kind == SubmissionType.PAPER:
                return False
        
        # Check if conference is paper-only (no abstract deadline)
        if (SubmissionType.PAPER in conference.deadlines and 
            SubmissionType.ABSTRACT not in conference.deadlines):
            # Paper-only conference - abstracts cannot be assigned
            if submission.kind == SubmissionType.ABSTRACT:
                return False
        
        # Check engineering vs medical compatibility
        if submission.engineering:
            # Engineering paper
            if conference.conf_type == ConferenceType.MEDICAL:
                # Engineering paper to medical conference - allowed but with penalty
                return True
            elif conference.conf_type == ConferenceType.ENGINEERING:
                # Engineering paper to engineering conference - optimal
                return True
        else:
            # Medical/Clinical paper
            if conference.conf_type == ConferenceType.ENGINEERING:
                # Medical paper to engineering conference - not recommended
                return False
            elif conference.conf_type == ConferenceType.MEDICAL:
                # Medical paper to medical conference - optimal
                return True
        
        return True
    

    def _calculate_earliest_start_date(self, submission: Submission) -> date:
        """Calculate the earliest start date for a submission based on dependencies and constraints."""
        # If explicitly set, use it
        if submission.earliest_start_date:
            return submission.earliest_start_date
        
        # Start with today as the earliest possible date
        earliest_date = date.today()
        
        # Check dependencies - submission must start after all dependencies are completed
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in self.submissions:
                    dep = self.submissions[dep_id]
                    # Calculate when this dependency would end if scheduled today
                    dep_duration = dep.get_duration_days(self.config)
                    dep_end_date = date.today() + timedelta(days=dep_duration)
                    # This submission must start after the dependency ends
                    earliest_date = max(earliest_date, dep_end_date)
        
        # Check conference deadline and work backwards
        if submission.conference_id and submission.conference_id in self.conferences:
            conf = self.conferences[submission.conference_id]
            if submission.kind in conf.deadlines:
                deadline = conf.deadlines[submission.kind]
                # Work backwards from deadline
                lead_time = self.config.min_paper_lead_time_days
                if submission.kind.value == "ABSTRACT":
                    lead_time = self.config.min_abstract_lead_time_days
                
                # Calculate latest possible start date to meet deadline
                latest_start = deadline - timedelta(days=lead_time)
                # Add buffer to ensure we have enough time
                latest_start_with_buffer = latest_start - timedelta(days=SCHEDULING_CONSTANTS.lookahead_window_days)
                # Earliest date must be before the latest start date
                earliest_date = min(earliest_date, latest_start_with_buffer)
        
        return earliest_date
    
    def _get_scheduling_window(self) -> tuple[date, date]:
        """Get the scheduling window (start and end dates) for all submissions."""
        # Start with today as the minimum start date
        today = date.today()
        start_date = today
        
        # Collect all relevant dates for end date calculation
        dates = []
        
        # Add explicit earliest start dates (but don't allow past dates)
        for submission in self.submissions.values():
            if submission.earliest_start_date:
                # Only consider future dates
                if submission.earliest_start_date >= today:
                    dates.append(submission.earliest_start_date)
            else:
                # Calculate implicit earliest start date
                calculated_start = self._calculate_earliest_start_date(submission)
                if calculated_start >= today:
                    dates.append(calculated_start)
        
        # Add conference deadlines (only future ones)
        for conference in self.conferences.values():
            for deadline in conference.deadlines.values():
                if deadline >= today:
                    dates.append(deadline)
        
        # If we have future dates, use the earliest one as start
        if dates:
            earliest_future_date = min(dates)
            # Use the later of today or the earliest future date
            start_date = max(today, earliest_future_date)
        
        # Calculate end date based on actual conference deadlines
        if self.conferences:
            latest_deadlines = []
            for conf in self.conferences.values():
                for deadline in conf.deadlines.values():
                    if deadline >= today:  # Only consider future deadlines
                        latest_deadlines.append(deadline)
            if latest_deadlines:
                latest_deadline = max(latest_deadlines)
                end_date = latest_deadline + timedelta(days=SCHEDULING_CONSTANTS.conference_response_time_days)
            else:
                end_date = start_date + timedelta(days=365)  # 1 year from start as fallback
        else:
            end_date = start_date + timedelta(days=365)  # 1 year from start as fallback
        
        return start_date, end_date
    
    def _schedule_early_abstracts(self, schedule: Dict[str, date], abstract_advance: int):
        """Schedule abstracts early if enabled."""
        abstracts = [sid for sid, sub in self.submissions.items() 
                    if sub.kind == SubmissionType.ABSTRACT]
        
        for abstract_id in abstracts:
            abstract = self.submissions[abstract_id]
            if abstract.conference_id and abstract.conference_id in self.conferences:
                conf = self.conferences[abstract.conference_id]
                if SubmissionType.ABSTRACT in conf.deadlines:
                    early_date = conf.deadlines[SubmissionType.ABSTRACT] - timedelta(days=abstract_advance)
                    if abstract.earliest_start_date is None or early_date >= abstract.earliest_start_date:
                        schedule[abstract_id] = early_date 