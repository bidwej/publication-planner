"""Core data types and models."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from enum import Enum
from dateutil.parser import parse as parse_date

from pydantic import BaseModel, Field, ConfigDict

from .constants import SCHEDULING_CONSTANTS, PENALTY_CONSTANTS, EFFICIENCY_CONSTANTS, SCORING_CONSTANTS

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
    
    def get_start_date(self, submission_id: str) -> Optional[date]:
        """Get start date for a submission."""
        interval = self.intervals.get(submission_id)
        return interval.start_date if interval else None
    
    def get_end_date(self, submission_id: str) -> Optional[date]:
        """Get end date for a submission."""
        interval = self.intervals.get(submission_id)
        return interval.end_date if interval else None
    
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
    
    def validate_submission(self) -> List[str]:
        """Validate submission and return list of errors."""
        try:
            from validation.submission import validate_submission_basic
            return validate_submission_basic(self)
        except ImportError:
            # Fallback to basic validation if validation modules not available
            errors = []
            if not self.id:
                errors.append("Missing submission ID")
            if not self.title:
                errors.append("Missing title")
            if self.draft_window_months < 0:
                errors.append("Draft window months cannot be negative")
            if self.lead_time_from_parents < 0:
                errors.append("Lead time from parents cannot be negative")
            return errors
    
    def get_priority_score(self, config: 'Config') -> float:
        """Calculate priority score based on config weights."""
        if not config.priority_weights:
            return 1.0
        
        # For abstracts that are required for papers, inherit the paper's priority
        if self.kind == SubmissionType.ABSTRACT and self._is_required_abstract(config):
            # Required abstracts get paper priority, not abstract priority
            type_key = "paper"
        else:
            # Normal priority based on submission type
            type_key = self.kind.value  # "paper", "abstract", etc.
            
        base_weight = config.priority_weights.get(type_key, 1.0)
        
        # Engineering bonus
        if self.engineering:  # Engineering submissions get bonus
            engineering_bonus = config.priority_weights.get("engineering_paper", 2.0)
            base_weight *= engineering_bonus
        
        return base_weight
    
    def _is_required_abstract(self, config: 'Config') -> bool:
        """Check if this abstract is required for a paper submission."""
        if self.kind != SubmissionType.ABSTRACT:
            return False
            
        # Check if this abstract ID matches the pattern for required abstracts
        # Required abstracts have IDs like "paper1-abs-conf1"
        if '-abs-' not in self.id:
            return False
            
        # Find if there's a corresponding paper that depends on this abstract
        for submission in config.submissions:
            if (submission.kind == SubmissionType.PAPER and 
                submission.depends_on and 
                self.id in submission.depends_on):
                return True
                
        return False
    
    def are_dependencies_satisfied(self, schedule: 'Schedule', 
                                  submissions_dict: Dict[str, 'Submission'], 
                                  config: 'Config', current_date: date) -> bool:
        """Check if all dependencies are satisfied for this submission."""
        if not self.depends_on:
            return True
        
        for dep_id in (self.depends_on or []):
            # Check if dependency exists
            if dep_id not in submissions_dict:
                return False
            
            # Check if dependency is scheduled
            if dep_id not in schedule.intervals:
                return False
            dep_start = schedule.intervals[dep_id].start_date
            
            # Check if dependency is completed
            dep = submissions_dict[dep_id]
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
    
    @property
    def effective_submission_types(self) -> SubmissionWorkflow:
        """Get submission types, auto-determined from deadlines if not explicitly set."""
        return self.submission_types if self.submission_types is not None else self._determine_submission_type()
    
    def _determine_submission_type(self) -> SubmissionWorkflow:
        """Determine submission type based on available deadlines."""
        has_abstract = SubmissionType.ABSTRACT in self.deadlines
        has_paper = SubmissionType.PAPER in self.deadlines
        has_poster = SubmissionType.POSTER in self.deadlines
        
        if has_abstract and has_paper and has_poster:
            return SubmissionWorkflow.ALL_TYPES
        elif has_abstract and has_paper:
            # Default to ABSTRACT_OR_PAPER unless explicitly specified as requiring abstract before paper
            # This means the conference accepts either abstracts OR papers, not necessarily both in sequence
            return SubmissionWorkflow.ABSTRACT_OR_PAPER
        elif has_abstract and not has_paper:
            return SubmissionWorkflow.ABSTRACT_ONLY
        elif has_paper and not has_abstract:
            return SubmissionWorkflow.PAPER_ONLY
        elif has_poster and not has_abstract and not has_paper:
            return SubmissionWorkflow.POSTER_ONLY
        else:
            return SubmissionWorkflow.ABSTRACT_OR_PAPER
    
    def accepts_submission_type(self, submission_type: SubmissionType) -> bool:
        """Check if conference accepts this submission type."""
        if self.effective_submission_types == SubmissionWorkflow.ALL_TYPES:
            return True
        elif self.effective_submission_types == SubmissionWorkflow.ABSTRACT_ONLY:
            return submission_type == SubmissionType.ABSTRACT
        elif self.effective_submission_types == SubmissionWorkflow.PAPER_ONLY:
            return submission_type == SubmissionType.PAPER
        elif self.effective_submission_types == SubmissionWorkflow.POSTER_ONLY:
            return submission_type == SubmissionType.POSTER
        elif self.effective_submission_types == SubmissionWorkflow.ABSTRACT_THEN_PAPER:
            return submission_type in [SubmissionType.ABSTRACT, SubmissionType.PAPER]
        elif self.effective_submission_types == SubmissionWorkflow.ABSTRACT_OR_PAPER:
            return submission_type in [SubmissionType.ABSTRACT, SubmissionType.PAPER]
        return False
    
    def requires_abstract_before_paper(self) -> bool:
        """Check if conference requires abstract submission before paper submission."""
        return self.effective_submission_types == SubmissionWorkflow.ABSTRACT_THEN_PAPER
    
    def get_required_dependencies(self, submission_type: SubmissionType) -> List[str]:
        """Get list of required dependencies for this submission type at this conference."""
        # Dependencies are handled at the submission level, not conference level
        return []
    
    def is_compatible_with_submission(self, submission: 'Submission') -> bool:
        """Check if a submission is compatible with this conference."""
        candidate_types = submission.preferred_kinds if submission.preferred_kinds else [submission.kind]
        
        for submission_type in candidate_types:
            if submission_type in self.deadlines:
                break
        else:
            return False
        
        if submission.engineering:
            return True
        else:
            return self.conf_type != ConferenceType.ENGINEERING
    
    def get_submission_compatibility_errors(self, submission: 'Submission') -> List[str]:
        """Get list of compatibility errors between submission and conference."""
        errors = []
        
        candidate_types = submission.preferred_kinds if submission.preferred_kinds else [submission.kind]
        
        compatible_type = None
        for submission_type in candidate_types:
            if self.accepts_submission_type(submission_type):
                compatible_type = submission_type
                break
        
        if compatible_type is None:
            types_str = ", ".join([t.value for t in candidate_types])
            errors.append(f"Conference {self.id} does not accept any of the requested submission types: {types_str}")
        
        return errors
    

    
    def validate_conference(self) -> List[str]:
        """Validate conference and return list of errors."""
        try:
            from validation.venue import validate_conference_basic
            return validate_conference_basic(self)
        except ImportError:
            # Fallback to basic validation if validation modules not available
            errors = []
            if not self.id:
                errors.append("Missing conference ID")
            if not self.name:
                errors.append("Missing conference name")
            if not self.deadlines:
                errors.append("No deadlines defined")
            return errors
    
    def get_deadline(self, submission_type: SubmissionType) -> Optional[date]:
        """Get deadline for a specific submission type."""
        return self.deadlines.get(submission_type)
    
    def has_deadline(self, submission_type: SubmissionType) -> bool:
        """Check if conference has deadline for submission type."""
        return submission_type in self.deadlines

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
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors."""
        try:
            from validation.config import validate_config_basic
            return validate_config_basic(self)
        except ImportError:
            # Fallback to basic validation if validation modules not available
            errors = []
            if not self.submissions:
                errors.append("No submissions defined")
            if not self.conferences:
                errors.append("No conferences defined")
            if self.min_abstract_lead_time_days < 0:
                errors.append("Min abstract lead time cannot be negative")
            if self.min_paper_lead_time_days < 0:
                errors.append("Min paper lead time cannot be negative")
            if self.max_concurrent_submissions < 1:
                errors.append("Max concurrent submissions must be at least 1")
            return errors
    
    # Computed properties
    @property
    def submissions_dict(self) -> Dict[str, Submission]:
        return {sub.id: sub for sub in self.submissions}
    
    @property
    def conferences_dict(self) -> Dict[str, Conference]:
        return {conf.id: conf for conf in self.conferences}
    
    @property
    def start_date(self) -> date:
        """Get the earliest start date for any submission."""
        if not self.submissions:
            return date.today()
        
        earliest_dates = []
        for submission in self.submissions:
            if submission.earliest_start_date:
                earliest_dates.append(submission.earliest_start_date)
            else:
                # Use a reasonable default if no earliest_start_date is set
                earliest_dates.append(date.today())
        
        return min(earliest_dates) if earliest_dates else date.today()
    
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
        
        # Find the latest deadline and add some buffer
        latest_deadlines = []
        for conference in self.conferences:
            for deadline in conference.deadlines.values():
                latest_deadlines.append(deadline)
        
        if latest_deadlines:
            latest_deadline = max(latest_deadlines)
            return latest_deadline + timedelta(days=SCHEDULING_CONSTANTS.conference_response_time_days)  # 3 months buffer after latest deadline
        else:
            return date.today() + timedelta(days=365)

# ===== VALIDATION MODELS =====

class ValidationResult(BaseModel):
    """Unified validation result combining all constraint types."""
    is_valid: bool
    violations: List['ConstraintViolation']
    deadline_validation: 'DeadlineValidation'
    dependency_validation: 'DependencyValidation'
    resource_validation: 'ResourceValidation'
    summary: str

# ===== SCORING MODELS =====

class ScoringResult(BaseModel):
    """Unified scoring result combining all scoring types."""
    penalty_score: float
    quality_score: float
    efficiency_score: float
    penalty_breakdown: 'PenaltyBreakdown'
    efficiency_metrics: 'EfficiencyMetrics'
    timeline_metrics: 'TimelineMetrics'
    overall_score: float

# ===== SCHEDULING MODELS =====

class ScheduleResult(BaseModel):
    """Complete schedule result with all metrics and analysis."""
    schedule: 'Schedule'
    summary: 'ScheduleSummary'
    metrics: 'ScheduleMetrics'
    tables: Dict[str, List[Dict[str, str]]]
    validation: ValidationResult
    scoring: ScoringResult

# ===== VALIDATION MODELS =====

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
    deadline: date
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

class ConstraintValidation(BaseModel):
    """Result of constraint validation."""
    is_valid: bool
    violations: List[ConstraintViolation]
    summary: str

class DeadlineValidation(ConstraintValidation):
    """Result of deadline validation."""
    compliance_rate: float
    total_submissions: int
    compliant_submissions: int

class DependencyValidation(ConstraintValidation):
    """Result of dependency validation."""
    satisfaction_rate: float
    total_dependencies: int
    satisfied_dependencies: int

class ResourceValidation(ConstraintValidation):
    """Result of resource validation."""
    max_concurrent: int
    max_observed: int
    total_days: int

class PenaltyBreakdown(BaseModel):
    """Breakdown of penalty costs."""
    total_penalty: float
    deadline_penalties: float
    dependency_penalties: float
    resource_penalties: float
    conference_compatibility_penalties: float
    abstract_paper_dependency_penalties: float

class EfficiencyMetrics(BaseModel):
    """Resource efficiency metrics."""
    utilization_rate: float
    peak_utilization: int
    avg_utilization: float
    efficiency_score: float

class TimelineMetrics(BaseModel):
    """Timeline efficiency metrics."""
    duration_days: int
    avg_daily_load: float
    timeline_efficiency: float

# ===== ANALYTICS MODELS =====

class AnalyticsResult(BaseModel):
    """Base class for all analytics results."""
    summary: str
    metadata: Optional[Dict[str, Any]] = None

class ScheduleAnalysis(AnalyticsResult):
    """Analysis of schedule completeness."""
    scheduled_count: int
    total_count: int
    completion_rate: float
    missing_submissions: List[Dict[str, Any]]

class ScheduleDistribution(AnalyticsResult):
    """Distribution of submissions over time."""
    monthly_distribution: Dict[str, int]
    quarterly_distribution: Dict[str, int]
    yearly_distribution: Dict[str, int]

class SubmissionTypeAnalysis(AnalyticsResult):
    """Analysis of submission types."""
    type_counts: Dict[str, int]
    type_percentages: Dict[str, float]

class TimelineAnalysis(AnalyticsResult):
    """Timeline analysis results."""
    start_date: Optional[date]
    end_date: Optional[date]
    duration_days: int
    avg_submissions_per_month: float

class ResourceAnalysis(AnalyticsResult):
    """Resource analysis results."""
    peak_load: int
    avg_load: float
    utilization_pattern: Dict[date, int]

# ===== OUTPUT DATA MODELS =====

class ScheduleSummary(BaseModel):
    """Summary metrics for a schedule."""
    total_submissions: int
    schedule_span: int
    start_date: Optional[date]
    end_date: Optional[date]
    penalty_score: float
    quality_score: float
    efficiency_score: float
    deadline_compliance: float
    resource_utilization: float
    


class ScheduleMetrics(BaseModel):
    """Detailed metrics for a schedule."""
    makespan: int
    avg_utilization: float
    peak_utilization: int
    total_penalty: float
    compliance_rate: float
    quality_score: float



class ConstraintValidationResult(BaseModel):
    """Result of all constraint validations."""
    deadlines: DeadlineValidation
    dependencies: DependencyValidation
    resources: ResourceValidation
    is_valid: bool 

class ScheduleState(BaseModel):
    """Complete state of a schedule for serialization."""
    model_config = ConfigDict(validate_assignment=True)
    
    schedule: 'Schedule'
    config: Config
    strategy: SchedulerStrategy
    timestamp: str
    version: str = "1.0"
    


 
