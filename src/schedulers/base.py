"""Base scheduler implementation."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional
from datetime import date, timedelta
from src.core.models import (
    Config, Submission, SubmissionType, SchedulerStrategy, Conference,
    generate_abstract_id, create_abstract_submission, ensure_abstract_paper_dependency
)
from src.validation import validate_deadline_compliance_single, validate_dependencies_satisfied, is_working_day


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
        return validate_dependencies_satisfied(sub, schedule, self.submissions, self.config, current)
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate end date for a submission."""
        lead_time = self.config.min_paper_lead_time_days
        if sub.kind.value == "ABSTRACT":
            lead_time = self.config.min_abstract_lead_time_days
        return start + timedelta(days=lead_time)
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline."""
        return validate_deadline_compliance_single(start, sub, self.config)
    
    # VALIDATION METHODS - Call comprehensive validation from constraints.py
    # These methods provide fast boolean validation during scheduling by calling
    # the comprehensive validation functions from constraints.py
    
    def _validate_all_constraints(self, sub: Submission, start: date, schedule: Dict[str, date]) -> bool:
        """Validate all constraints for a submission at a given start date."""
        from src.validation import validate_single_submission_constraints
        return validate_single_submission_constraints(sub, start, schedule, self.config)
    
    def _auto_link_abstract_paper(self):
        """Auto-link abstracts to papers and create missing abstract submissions."""
        submissions_dict = self.config.submissions_dict
        conferences_dict = self.config.conferences_dict
        
        # Track papers that need abstracts
        papers_needing_abstracts = []
        
        # Find papers that need abstract submissions
        papers_to_process = list(submissions_dict.items())
        for submission_id, submission in papers_to_process:
            if (submission.kind == SubmissionType.PAPER and 
                submission.conference_id and 
                submission.conference_id in conferences_dict):
                
                conf = conferences_dict[submission.conference_id]
                
                # Check if conference requires abstract before paper
                if conf.requires_abstract_before_paper():
                    # Generate abstract ID
                    abstract_id = generate_abstract_id(submission_id, submission.conference_id)
                    
                    # Check if abstract already exists
                    if abstract_id not in submissions_dict:
                        # Create abstract submission
                        abstract_submission = create_abstract_submission(
                            submission, submission.conference_id, 
                            self.config.penalty_costs or {}
                        )
                        
                        # Add to config submissions
                        self.config.submissions.append(abstract_submission)
                        submissions_dict[abstract_id] = abstract_submission
                        
                        # Ensure paper depends on abstract
                        ensure_abstract_paper_dependency(submission, abstract_id)
                        
                        papers_needing_abstracts.append(submission_id)
        
        # Update submissions dict after adding new submissions
        self.submissions = {s.id: s for s in self.config.submissions}
        
        if papers_needing_abstracts:
            print(f"Created {len(papers_needing_abstracts)} abstract submissions for papers: {papers_needing_abstracts}")
    
    def _assign_conferences(self, schedule: Dict[str, date]) -> Dict[str, date]:
        """Assign conferences to papers based on candidate_conferences and availability."""
        submissions_dict = self.config.submissions_dict
        conferences_dict = self.config.conferences_dict
        
        # Find papers that need conference assignment (generic papers without conference_id)
        papers_needing_assignment = []
        for submission_id, submission in submissions_dict.items():
            if (submission.kind == SubmissionType.PAPER and 
                not submission.conference_id and 
                submission.candidate_conferences):
                papers_needing_assignment.append(submission_id)
        
        # Simple assignment: pick first available conference from family
        for paper_id in papers_needing_assignment:
            submission = submissions_dict[paper_id]
            
            # Find compatible conferences from the family
            compatible_conferences = []
            for conf_id, conference in conferences_dict.items():
                # Check if conference name matches any of the candidate conferences
                if (submission.candidate_conferences and 
                    conference.name in submission.candidate_conferences):
                    
                    # Check conference compatibility matrix from README
                    is_compatible = self._check_conference_compatibility(submission, conference)
                    if is_compatible:
                        compatible_conferences.append(conf_id)
            
            # Assign to first compatible conference with available deadline
            for conf_id in compatible_conferences:
                conference = conferences_dict[conf_id]
                if submission.kind in conference.deadlines:
                    # Update the submission with the assigned conference
                    submission.conference_id = conf_id
                    break
        
        return schedule
    
    def _check_conference_compatibility(self, submission: Submission, conference: 'Conference') -> bool:
        """Check if a submission is compatible with a conference based on the compatibility matrix."""
        from src.core.models import ConferenceType
        
        # Check if conference accepts the submission type
        if submission.kind not in conference.deadlines:
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
                latest_start_with_buffer = latest_start - timedelta(days=30)
                # Earliest date must be before the latest start date
                earliest_date = min(earliest_date, latest_start_with_buffer)
        
        return earliest_date
    
    def _get_scheduling_window(self) -> tuple[date, date]:
        """Get the scheduling window (start and end dates) for all submissions."""
        # Collect all relevant dates
        dates = []
        
        # Add explicit earliest start dates
        for submission in self.submissions.values():
            if submission.earliest_start_date:
                dates.append(submission.earliest_start_date)
            else:
                # Calculate implicit earliest start date
                dates.append(self._calculate_earliest_start_date(submission))
        
        # Add conference deadlines
        for conference in self.conferences.values():
            dates.extend(conference.deadlines.values())
        
        # Add today's date as fallback
        dates.append(date.today())
        
        # Calculate window
        start_date = min(dates)
        
        # Calculate end date based on actual conference deadlines
        if self.conferences:
            latest_deadlines = []
            for conf in self.conferences.values():
                latest_deadlines.extend(conf.deadlines.values())
            if latest_deadlines:
                latest_deadline = max(latest_deadlines)
                end_date = latest_deadline + timedelta(days=90)  # 3 months buffer after latest deadline
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