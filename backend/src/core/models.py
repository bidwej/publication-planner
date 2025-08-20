"""Core data types and models."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from enum import Enum
from dateutil.parser import parse as parse_date

from pydantic import BaseModel, Field, ConfigDict

from core.constants import SCHEDULING_CONSTANTS, PENALTY_CONSTANTS, EFFICIENCY_CONSTANTS, SCORING_CONSTANTS

# Forward imports to avoid circular dependencies
# These will be imported locally in methods that need them
# from validation.schedule import validate_schedule_constraints

class SubmissionType(str, Enum):
    """Types of submissions."""
    PAPER = "paper"
    ABSTRACT = "abstract"
    POSTER = "poster"


class SubmissionWorkflow(str, Enum):
    """Workflow patterns for submissions."""
    ABSTRACT_ONLY = "abstract_only"           # Just submit abstract
    PAPER_ONLY = "paper_only"                # Just submit paper
    POSTER_ONLY = "poster_only"              # Just submit poster
    ABSTRACT_THEN_PAPER = "abstract_then_paper"  # Engineering: abstract → paper
    ABSTRACT_OR_PAPER = "abstract_or_paper"      # Medical: either/or
    ALL_TYPES = "all_types"                  # Accept everything

class SchedulerStrategy(str, Enum):
    """Available scheduling strategies."""
    GREEDY = "greedy"
    STOCHASTIC = "stochastic"
    LOOKAHEAD = "lookahead"
    BACKTRACKING = "backtracking"
    RANDOM = "random"
    HEURISTIC = "heuristic"
    OPTIMAL = "optimal"
    ADVANCED = "advanced"


class Interval(BaseModel):
    """A time interval with start and end dates."""
    start_date: date
    end_date: date
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days

class Schedule(BaseModel):
    """A schedule mapping submission IDs to their time intervals."""
    model_config = ConfigDict(validate_assignment=True)
    
    intervals: Dict[str, Interval] = Field(
        default_factory=dict,
        description="Submission ID -> Interval mapping"
    )
    
    def add_interval(self, submission_id: str, start_date: date, end_date: Optional[date] = None, 
                    duration_days: Optional[int] = None) -> None:
        """Add or update an interval for a submission."""
        if end_date is None and duration_days is not None:
            end_date = start_date + timedelta(days=duration_days)
        elif end_date is None:
            end_date = start_date + timedelta(days=30)  # Default duration
        
        self.intervals[submission_id] = Interval(start_date=start_date, end_date=end_date)
    
    def has_submission(self, submission_id: str) -> bool:
        """Check if a submission is scheduled."""
        return submission_id in self.intervals
    
    def __len__(self) -> int:
        """Return number of scheduled submissions."""
        return len(self.intervals)
    
    def __contains__(self, submission_id: str) -> bool:
        """Check if submission is scheduled."""
        return submission_id in self.intervals
    
    @property
    def start_date(self) -> Optional[date]:
        """Get the earliest start date across all scheduled submissions."""
        if not self.intervals:
            return None
        return min(interval.start_date for interval in self.intervals.values())
    
    @property
    def end_date(self) -> Optional[date]:
        """Get the latest end date across all scheduled submissions."""
        if not self.intervals:
            return None
        return max(interval.end_date for interval in self.intervals.values())
    
    def calculate_duration_days(self) -> int:
        """
        Calculate the duration of the schedule in days.
        
        Returns
        -------
        int
            Duration in days from earliest to latest start date
        """
        if not self.intervals:
            return 0
        
        dates = [interval.start_date for interval in self.intervals.values()]
        return (max(dates) - min(dates)).days if dates else 0
    

    


class Submission(BaseModel):
    """A submission to a conference."""
    model_config = ConfigDict(validate_assignment=True)
    
    id: str
    title: str
    kind: SubmissionType  # Base type (PAPER for both mods and ed papers)
    author: Optional[str] = None  # Explicit author field ("pccp" or "ed")
    conference_id: Optional[str] = None  # Optional - None for work items
    depends_on: Optional[List[str]] = None
    draft_window_months: int = 3
    lead_time_from_parents: int = 0
    penalty_cost_per_day: Optional[float] = None
    earliest_start_date: Optional[date] = None
    preferred_conferences: Optional[List[str]] = None  # Suggested conferences
    preferred_kinds: Optional[List[SubmissionType]] = None  # Preferred submission types at conferences (in priority order)
    preferred_workflow: Optional[SubmissionWorkflow] = None  # User's preferred workflow (suggestion, not requirement)
    submission_workflow: Optional[SubmissionWorkflow] = None  # How this submission should be handled (system-determined)
    
    engineering: bool = False  # Whether this is an engineering submission
    
    # Additional fields for unified schema (both mods and papers now have these)
    engineering_ready_date: Optional[date] = None  # When engineering work completes and data is available
    free_slack_months: Optional[int] = None  # Buffer time in months
    penalty_cost_per_month: Optional[float] = None  # Monthly penalty cost for delays
    

    

    
    def are_dependencies_satisfied(self, schedule: 'Schedule', 
                                  config: 'Config', current_date: date) -> bool:
        """Check if all dependencies are satisfied for this submission."""
        if not self.depends_on:
            return True
        
        for dep_id in (self.depends_on or []):
            # Check if dependency exists
            dep = config.get_submission(dep_id)
            if not dep:
                return False
            
            # Check if dependency is scheduled
            if dep_id not in schedule.intervals:
                return False
            dep_start = schedule.intervals[dep_id].start_date
            
            # Check if dependency is completed
            dep_end = dep.get_end_date(dep_start, config)
            
            if current_date < dep_end:
                return False
        
        return True
    
    def get_duration_days(self, config: 'Config') -> int:
        """Calculate the duration in days for this submission."""
        days_per_month = SCHEDULING_CONSTANTS.days_per_month
        
        if self.kind == SubmissionType.ABSTRACT:
            work_item_duration = getattr(config, 'work_item_duration_days', 14)
            return work_item_duration
        if self.kind == SubmissionType.POSTER:
            if self.draft_window_months > 0:
                return self.draft_window_months * days_per_month
            return SCHEDULING_CONSTANTS.poster_duration_days
        # SubmissionType.PAPER - use draft_window_months or fall back to config
        if self.draft_window_months > 0:
            return self.draft_window_months * days_per_month
        return config.min_paper_lead_time_days
    
    def get_end_date(self, start_date: date, config: 'Config') -> date:
        """Calculate the end date for this submission starting on the given date."""
        duration_days = self.get_duration_days(config)
        return start_date + timedelta(days=duration_days)
    
    # Validation logic moved to validation/submission.py
    
    def get_priority_score(self, config: 'Config') -> float:
        """Calculate priority score for this submission."""
        base_score = 1.0
        
        # Apply type-based weights if available
        if config.priority_weights:
            if self.kind == SubmissionType.ABSTRACT:
                base_score = config.priority_weights.get("abstract", 0.5)
            elif self.kind == SubmissionType.PAPER:
                if self.engineering:
                    base_score = config.priority_weights.get("engineering_paper", 2.0)
                else:
                    base_score = config.priority_weights.get("paper", 1.0)
            elif self.kind == SubmissionType.POSTER:
                base_score = config.priority_weights.get("poster", 0.8)
        
        return base_score

class ConferenceType(str, Enum):
    """Types of conferences."""
    MEDICAL = "MEDICAL"
    ENGINEERING = "ENGINEERING"

class ConferenceRecurrence(str, Enum):
    """Conference recurrence patterns."""
    ANNUAL = "annual"
    BIENNIAL = "biennial"
    QUARTERLY = "quarterly"

class Conference(BaseModel):
    """A conference with deadlines."""
    model_config = ConfigDict(validate_assignment=True)
    
    id: str
    name: str
    conf_type: ConferenceType
    recurrence: ConferenceRecurrence
    deadlines: Dict[SubmissionType, date]
    submission_types: Optional[SubmissionWorkflow] = None  # What types of submissions are accepted
    max_submissions_per_author: Optional[int] = None  # Maximum submissions allowed per author
    
    @property
    def effective_submission_types(self) -> SubmissionWorkflow:
        """Get submission types, auto-determined from deadlines if not explicitly set."""
        return self.submission_types if self.submission_types is not None else self._determine_submission_type()
    
    def _determine_submission_type(self) -> SubmissionWorkflow:
        """Determine submission type based on available deadlines."""
        types = {SubmissionType.ABSTRACT, SubmissionType.PAPER, SubmissionType.POSTER}
        available = types & set(self.deadlines.keys())
        
        if len(available) == 3:
            return SubmissionWorkflow.ALL_TYPES
        elif {SubmissionType.ABSTRACT, SubmissionType.PAPER} <= available:
            return SubmissionWorkflow.ABSTRACT_OR_PAPER
        elif SubmissionType.ABSTRACT in available:
            return SubmissionWorkflow.ABSTRACT_ONLY
        elif SubmissionType.PAPER in available:
            return SubmissionWorkflow.PAPER_ONLY
        elif SubmissionType.POSTER in available:
            return SubmissionWorkflow.POSTER_ONLY
        else:
            return SubmissionWorkflow.ABSTRACT_OR_PAPER
    
    def accepts_submission_type(self, submission_type: SubmissionType) -> bool:
        """Check if conference accepts this submission type."""
        workflow = self.effective_submission_types
        
        if workflow == SubmissionWorkflow.ALL_TYPES:
            return True
        elif workflow in (SubmissionWorkflow.ABSTRACT_ONLY, SubmissionWorkflow.PAPER_ONLY, SubmissionWorkflow.POSTER_ONLY):
            return submission_type.value == workflow.value.split('_')[0]
        elif workflow in (SubmissionWorkflow.ABSTRACT_THEN_PAPER, SubmissionWorkflow.ABSTRACT_OR_PAPER):
            return submission_type in (SubmissionType.ABSTRACT, SubmissionType.PAPER)
        
        return False
    
    def requires_abstract_before_paper(self) -> bool:
        """Check if conference requires abstract submission before paper submission."""
        return self.effective_submission_types == SubmissionWorkflow.ABSTRACT_THEN_PAPER
    
    def is_compatible_with_submission(self, submission: 'Submission') -> bool:
        """Check if a submission is compatible with this conference."""
        candidate_types = submission.preferred_kinds or [submission.kind]
        
        # Check if any submission type is accepted
        if not any(self.accepts_submission_type(st) for st in candidate_types):
            return False
        
        # Engineering submissions can go anywhere, medical only to medical venues
        return submission.engineering or self.conf_type != ConferenceType.ENGINEERING
    

    

    

    
    def get_deadline(self, submission_type: SubmissionType) -> Optional[date]:
        """Get deadline for a specific submission type."""
        return self.deadlines.get(submission_type)
    
    def has_deadline(self, submission_type: SubmissionType) -> bool:
        """Check if conference has deadline for submission type."""
        return submission_type in self.deadlines
    
    # Validation logic moved to validation/config.py

class Config(BaseModel):
    """Configuration for the scheduler."""
    model_config = ConfigDict(validate_assignment=True)
    
    submissions: List[Submission]
    conferences: List[Conference]
    min_abstract_lead_time_days: int
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    default_paper_lead_time_months: int = SCHEDULING_CONSTANTS.default_paper_lead_time_months
    work_item_duration_days: int = SCHEDULING_CONSTANTS.work_item_duration_days
    conference_response_time_days: int = SCHEDULING_CONSTANTS.conference_response_time_days
    max_backtrack_days: int = SCHEDULING_CONSTANTS.backtrack_limit_days
    randomness_factor: float = EFFICIENCY_CONSTANTS.randomness_factor
    lookahead_bonus_increment: float = EFFICIENCY_CONSTANTS.lookahead_bonus_increment
    penalty_costs: Optional[Dict[str, float]] = None
    priority_weights: Optional[Dict[str, float]] = None
    scheduling_options: Optional[Dict[str, Any]] = None
    blackout_dates: Optional[List[date]] = None
    data_files: Optional[Dict[str, str]] = None
    scheduling_start_date: Optional[date] = None  # When scheduling should begin (defaults to today)
    
    @classmethod
    def create_default(cls) -> 'Config':
        """Create a default configuration with minimal data for app initialization."""
        default_penalty_costs = {
            "default_mod_penalty_per_day": PENALTY_CONSTANTS.default_mod_penalty_per_day,
            "default_paper_penalty_per_day": PENALTY_CONSTANTS.default_paper_penalty_per_day
        }
        
        default_priority_weights = {
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        }
        
        default_scheduling_options = {
            "enable_blackout_periods": False,
            "enable_early_abstract_scheduling": False,
            "enable_working_days_only": False,
            "enable_priority_weighting": True,
            "enable_dependency_tracking": True,
            "enable_concurrency_control": True
        }
        
        return cls(
            submissions=[],  # Empty for app initialization
            conferences=[],  # Empty for app initialization
            min_abstract_lead_time_days=SCHEDULING_CONSTANTS.min_abstract_lead_time_days,
            min_paper_lead_time_days=SCHEDULING_CONSTANTS.min_paper_lead_time_days,
            max_concurrent_submissions=SCHEDULING_CONSTANTS.max_concurrent_submissions,
            default_paper_lead_time_months=SCHEDULING_CONSTANTS.default_paper_lead_time_months,
            penalty_costs=default_penalty_costs,
            priority_weights=default_priority_weights,
            scheduling_options=default_scheduling_options,
            blackout_dates=[],  # Empty when disabled
            data_files={
                "conferences": "conferences.json",
                "papers": "papers.json",
                "mods": "mods.json"
            }
        )
    

    
    # Type-safe access methods with better structure
    def get_submission(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID with type safety."""
        return next((sub for sub in self.submissions if sub.id == submission_id), None)
    
    def get_conference(self, conference_id: str) -> Optional[Conference]:
        """Get conference by ID with type safety."""
        return next((conf for conf in self.conferences if conf.id == conference_id), None)
    
    def has_submission(self, submission_id: str) -> bool:
        """Check if submission exists."""
        return any(sub.id == submission_id for sub in self.submissions)
    
    def has_conference(self, conference_id: str) -> bool:
        """Check if conference exists."""
        return any(conf.id == conference_id for conf in self.conferences)
    

    
    # Convenience helpers to avoid repetitive None checks in call sites
    def get_conference_name(self, conference_id: Optional[str], default: str = "N/A") -> str:
        """Safely get a conference name or return a default label.

        Parameters
        ----------
        conference_id: Optional[str]
            The conference identifier; may be None
        default: str
            Fallback label when conference is missing
        """
        if not conference_id:
            return default
        conference = self.get_conference(conference_id)
        return conference.name if conference else default

    def get_deadline_for(self, submission: 'Submission') -> Optional[date]:
        """Safely get the deadline for a submission's type at its conference.

        Returns None when conference or deadline is missing.
        """
        if not submission.conference_id:
            return None
        conference = self.get_conference(submission.conference_id)
        if not conference:
            return None
        return conference.deadlines.get(submission.kind)

    def get_deadline_for_type(self, conference_id: Optional[str], submission_type: 'SubmissionType') -> Optional[date]:
        """Safely get the deadline for a given submission type at a conference."""
        if not conference_id:
            return None
        conference = self.get_conference(conference_id)
        if not conference:
            return None
        return conference.deadlines.get(submission_type)
    
    # Validation logic moved to validation/config.py
    
    # Circular dependency detection moved to validation/config.py
    
    @property
    def start_date(self) -> date:
        """Get the earliest start date for any submission."""
        if not self.submissions:
            return date.today()
        
        earliest_dates = [
            submission.earliest_start_date or date.today()
            for submission in self.submissions
        ]
        return min(earliest_dates)
    
    @property
    def effective_scheduling_start_date(self) -> date:
        """Get when scheduling should begin (user preference or earliest submission date)."""
        # If user explicitly set a scheduling start date, use that
        if self.scheduling_start_date is not None:
            return self.scheduling_start_date
        
        # Otherwise, use the earliest submission date
        return self.start_date
    
    @property
    def end_date(self) -> date:
        """Get the latest deadline for any conference."""
        if not self.conferences:
            return date.today() + timedelta(days=365)
        
        # Find the latest deadline and add buffer
        all_deadlines = [
            deadline for conf in self.conferences 
            for deadline in conf.deadlines.values()
        ]
        
        if all_deadlines:
            return max(all_deadlines) + timedelta(days=SCHEDULING_CONSTANTS.conference_response_time_days)
        
        return date.today() + timedelta(days=365)

    @property
    def submissions_dict(self) -> Dict[str, Submission]:
        """Return a dictionary of submissions indexed by their ID."""
        return {sub.id: sub for sub in self.submissions}

    # Validation methods moved to validation modules

# ===== VALIDATION MODELS =====

class ValidationResult(BaseModel):
    """Generic validation result for all constraint types."""
    is_valid: bool
    violations: List['ConstraintViolation']
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Type-specific validation data")

# ===== SCHEDULING MODELS =====

class ConstraintViolation(BaseModel):
    """Base constraint violation."""
    submission_id: str
    description: str
    severity: str = "medium"

class DeadlineViolation(ConstraintViolation):
    """A deadline violation."""
    submission_title: str
    conference_id: str
    submission_type: str
    deadline: Optional[date]  # Can be None when no specific deadline is defined
    end_date: date
    days_late: int

class DependencyViolation(ConstraintViolation):
    """A dependency violation."""
    dependency_id: str
    issue: str  # "missing_dependency", "invalid_dependency", "timing_violation"
    days_violation: Optional[int] = None

class ResourceViolation(ConstraintViolation):
    """A resource constraint violation."""
    date: date
    load: int
    limit: int
    excess: int



# ===== ANALYTICS MODELS =====

# Note: All specific analytics models have been consolidated into ScheduleMetrics
# which now provides comprehensive schedule analysis in a single model

class ScheduleMetrics(BaseModel):
    """Complete schedule analysis and metrics in one comprehensive model."""
    # Core performance metrics
    makespan: int
    total_penalty: float
    compliance_rate: float
    quality_score: float
    
    # Penalty breakdown fields
    deadline_penalties: float = 0.0
    dependency_penalties: float = 0.0
    resource_penalties: float = 0.0
    conference_compatibility_penalties: float = 0.0
    abstract_paper_dependency_penalties: float = 0.0
    blackout_penalties: float = 0.0
    soft_block_penalties: float = 0.0
    single_conference_penalties: float = 0.0
    lead_time_penalties: float = 0.0
    slack_cost_penalties: float = 0.0
    
    # Resource utilization metrics
    avg_utilization: float
    peak_utilization: int
    utilization_rate: float
    efficiency_score: float
    
    # Timeline metrics
    duration_days: int
    avg_daily_load: float
    timeline_efficiency: float
    
    # Distribution data
    monthly_distribution: Dict[str, int] = Field(default_factory=dict)
    quarterly_distribution: Dict[str, int] = Field(default_factory=dict)
    yearly_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Submission breakdown
    submission_count: int = 0
    scheduled_count: int = 0
    completion_rate: float = 0.0
    type_counts: Dict[str, int] = Field(default_factory=dict)
    type_percentages: Dict[str, float] = Field(default_factory=dict)
    
    # Missing items
    missing_submissions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    

