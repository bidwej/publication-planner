"""Core data types and models."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date
from dataclasses import dataclass
from enum import Enum

from .constants import DAYS_PER_MONTH, DEFAULT_POSTER_DURATION_DAYS

class SubmissionType(str, Enum):
    """Types of submissions."""
    PAPER = "paper"
    ABSTRACT = "abstract"
    POSTER = "poster"

class SchedulerStrategy(str, Enum):
    """Available scheduling strategies."""
    GREEDY = "greedy"
    STOCHASTIC = "stochastic"
    LOOKAHEAD = "lookahead"
    BACKTRACKING = "backtracking"
    RANDOM = "random"
    HEURISTIC = "heuristic"
    OPTIMAL = "optimal"

@dataclass
class Submission:
    """A submission to a conference."""
    id: str
    title: str
    kind: SubmissionType
    conference_id: str
    depends_on: Optional[List[str]] = None
    draft_window_months: int = 3
    lead_time_from_parents: int = 0
    penalty_cost_per_day: Optional[float] = None
    engineering: bool = False
    earliest_start_date: Optional[date] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
    
    def validate(self) -> List[str]:
        """Validate submission and return list of errors."""
        errors = []
        if not self.id:
            errors.append("Missing submission ID")
        if not self.title:
            errors.append("Missing title")
        # Conference ID is optional for internal modules (mods)
        if not self.conference_id and not self.id.endswith("-wrk"):
            errors.append("Missing conference ID")
        if self.draft_window_months < 0:
            errors.append("Draft window months cannot be negative")
        if self.lead_time_from_parents < 0:
            errors.append("Lead time from parents cannot be negative")
        if self.penalty_cost_per_day is not None and self.penalty_cost_per_day < 0:
            errors.append("Penalty cost per day cannot be negative")
        return errors
    
    def get_priority_score(self, config: 'Config') -> float:
        """Calculate priority score based on config weights."""
        if not config.priority_weights:
            return 1.0
        
        # Base weight from submission type
        type_key = f"{self.kind.value}_paper" if self.kind == SubmissionType.PAPER else self.kind.value
        base_weight = config.priority_weights.get(type_key, 1.0)
        
        # Engineering bonus
        if self.engineering:
            engineering_bonus = config.priority_weights.get("engineering_paper", 2.0)
            base_weight *= engineering_bonus
        
        return base_weight
    
    def get_duration_days(self, config: 'Config') -> int:
        """Calculate the duration in days for this submission."""
        if self.kind == SubmissionType.ABSTRACT:
            return 0  # Abstracts are completed on the same day
        elif self.kind == SubmissionType.POSTER:
            # Posters typically have shorter duration than papers
            if self.draft_window_months > 0:
                return self.draft_window_months * DAYS_PER_MONTH
            else:
                return DEFAULT_POSTER_DURATION_DAYS
        else:  # SubmissionType.PAPER
            # Use draft_window_months if available, otherwise fall back to config
            if self.draft_window_months > 0:
                return self.draft_window_months * DAYS_PER_MONTH
            else:
                return config.min_paper_lead_time_days
    
    def get_end_date(self, start_date: date, config: 'Config') -> date:
        """Calculate the end date for this submission starting on the given date."""
        from datetime import timedelta
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

@dataclass
class Conference:
    """A conference with deadlines."""
    id: str
    name: str
    conf_type: ConferenceType
    recurrence: ConferenceRecurrence
    deadlines: Dict[SubmissionType, date]
    
    def validate(self) -> List[str]:
        """Validate conference and return list of errors."""
        errors = []
        if not self.id:
            errors.append("Missing conference ID")
        if not self.name:
            errors.append("Missing conference name")
        if not self.deadlines:
            errors.append("No deadlines defined")
        for submission_type, deadline in self.deadlines.items():
            if not isinstance(deadline, date):
                errors.append(f"Invalid deadline format for {submission_type}")
        return errors
    
    def get_deadline(self, submission_type: SubmissionType) -> Optional[date]:
        """Get deadline for a specific submission type."""
        return self.deadlines.get(submission_type)
    
    def has_deadline(self, submission_type: SubmissionType) -> bool:
        """Check if conference has deadline for submission type."""
        return submission_type in self.deadlines

@dataclass
class Config:
    """Configuration for the scheduler."""
    submissions: List[Submission]
    conferences: List[Conference]
    min_abstract_lead_time_days: int
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    default_paper_lead_time_months: int = 3
    penalty_costs: Optional[Dict[str, float]] = None
    priority_weights: Optional[Dict[str, float]] = None
    scheduling_options: Optional[Dict[str, Any]] = None
    blackout_dates: Optional[List[date]] = None
    data_files: Optional[Dict[str, str]] = None
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate basic requirements
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
        
        # Validate submissions
        submission_ids = set()
        for submission in self.submissions:
            submission_errors = submission.validate()
            errors.extend([f"Submission {submission.id}: {error}" for error in submission_errors])
            if submission.id in submission_ids:
                errors.append(f"Duplicate submission ID: {submission.id}")
            submission_ids.add(submission.id)
            
            # Validate conference reference
            if submission.conference_id:
                conference_ids = {conf.id for conf in self.conferences}
                if submission.conference_id not in conference_ids:
                    errors.append(f"Submission {submission.id} references unknown conference {submission.conference_id}")
        
        # Validate conferences
        conference_ids = set()
        for conference in self.conferences:
            conference_errors = conference.validate()
            errors.extend([f"Conference {conference.id}: {error}" for error in conference_errors])
            if conference.id in conference_ids:
                errors.append(f"Duplicate conference ID: {conference.id}")
            conference_ids.add(conference.id)
        
        return errors
    
    # Computed properties
    @property
    def submissions_dict(self) -> Dict[str, Submission]:
        return {sub.id: sub for sub in self.submissions}
    
    @property
    def conferences_dict(self) -> Dict[str, Conference]:
        return {conf.id: conf for conf in self.conferences}

# ===== UNIFIED VALIDATION MODELS =====

@dataclass
class ValidationResult:
    """Unified validation result combining all constraint types."""
    is_valid: bool
    violations: List['ConstraintViolation']
    deadline_validation: 'DeadlineValidation'
    dependency_validation: 'DependencyValidation'
    resource_validation: 'ResourceValidation'
    summary: str

# ===== UNIFIED SCORING MODELS =====

@dataclass
class ScoringResult:
    """Unified scoring result combining all scoring types."""
    penalty_score: float
    quality_score: float
    efficiency_score: float
    penalty_breakdown: 'PenaltyBreakdown'
    efficiency_metrics: 'EfficiencyMetrics'
    timeline_metrics: 'TimelineMetrics'
    overall_score: float

# ===== UNIFIED SCHEDULING MODELS =====

@dataclass
class Schedule:
    """A complete schedule with metadata."""
    assignments: Dict[str, date]
    config: Config
    metadata: Dict[str, Any]

@dataclass
class SchedulerResult:
    """Result from scheduler with metadata."""
    schedule: Dict[str, date]
    strategy: SchedulerStrategy
    execution_time: float
    iterations: int
    metadata: Dict[str, Any]

@dataclass
class ScheduleResult:
    """Complete schedule result with all metrics and tables."""
    schedule: Dict[str, date]
    summary: 'ScheduleSummary'
    metrics: 'ScheduleMetrics'
    tables: Dict[str, List[Dict[str, str]]]
    validation: ValidationResult
    scoring: ScoringResult

# ===== METRICS DATA MODELS =====

@dataclass
class ConstraintViolation:
    """A constraint violation."""
    submission_id: str
    description: str
    severity: str = "medium"

@dataclass
class DeadlineViolation:
    """A deadline violation."""
    submission_id: str
    description: str
    submission_title: str
    conference_id: str
    submission_type: str
    deadline: date
    end_date: date
    days_late: int
    severity: str = "medium"

@dataclass
class DependencyViolation:
    """A dependency violation."""
    submission_id: str
    description: str
    dependency_id: str
    issue: str  # "missing_dependency", "invalid_dependency", "timing_violation"
    days_violation: Optional[int] = None
    severity: str = "medium"

@dataclass
class ResourceViolation:
    """A resource constraint violation."""
    submission_id: str
    description: str
    date: date
    load: int
    limit: int
    excess: int
    severity: str = "medium"

@dataclass
class ConstraintValidation:
    """Result of constraint validation."""
    is_valid: bool
    violations: List[ConstraintViolation]
    summary: str

@dataclass
class DeadlineValidation(ConstraintValidation):
    """Result of deadline validation."""
    compliance_rate: float
    total_submissions: int
    compliant_submissions: int

@dataclass
class DependencyValidation(ConstraintValidation):
    """Result of dependency validation."""
    satisfaction_rate: float
    total_dependencies: int
    satisfied_dependencies: int

@dataclass
class ResourceValidation(ConstraintValidation):
    """Result of resource validation."""
    max_concurrent: int
    max_observed: int
    total_days: int

@dataclass
class PenaltyBreakdown:
    """Breakdown of penalty costs."""
    total_penalty: float
    deadline_penalties: float
    dependency_penalties: float
    resource_penalties: float

@dataclass
class EfficiencyMetrics:
    """Resource efficiency metrics."""
    utilization_rate: float
    peak_utilization: int
    avg_utilization: float
    efficiency_score: float

@dataclass
class TimelineMetrics:
    """Timeline efficiency metrics."""
    duration_days: int
    avg_daily_load: float
    timeline_efficiency: float

# ===== UNIFIED ANALYTICS BASE CLASS =====

@dataclass
class AnalyticsResult:
    """Base class for all analytics results."""
    summary: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ScheduleAnalysis:
    """Analysis of schedule completeness."""
    scheduled_count: int
    total_count: int
    completion_rate: float
    missing_submissions: List[Dict[str, Any]]
    summary: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ScheduleDistribution:
    """Distribution of submissions over time."""
    monthly_distribution: Dict[str, int]
    quarterly_distribution: Dict[str, int]
    yearly_distribution: Dict[str, int]
    summary: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SubmissionTypeAnalysis:
    """Analysis of submission types."""
    type_counts: Dict[str, int]
    type_percentages: Dict[str, float]
    summary: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TimelineAnalysis:
    """Timeline analysis results."""
    start_date: Optional[date]
    end_date: Optional[date]
    duration_days: int
    avg_submissions_per_month: float
    summary: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ResourceAnalysis:
    """Resource analysis results."""
    peak_load: int
    avg_load: float
    utilization_pattern: Dict[date, int]
    summary: str
    metadata: Optional[Dict[str, Any]] = None 

# ===== OUTPUT DATA MODELS =====

@dataclass
class ScheduleSummary:
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

@dataclass
class ScheduleMetrics:
    """Detailed metrics for a schedule."""
    makespan: int
    avg_utilization: float
    peak_utilization: int
    total_penalty: float
    compliance_rate: float
    quality_score: float

@dataclass
class CompleteOutput:
    """Complete output data for a schedule."""
    schedule: Dict[str, date]
    summary_metrics: ScheduleSummary
    detailed_metrics: ScheduleMetrics
    schedule_table: List[Dict[str, str]]
    metrics_table: List[Dict[str, str]]
    deadline_table: List[Dict[str, str]]

@dataclass
class ConstraintValidationResult:
    """Result of all constraint validations."""
    deadlines: DeadlineValidation
    dependencies: DependencyValidation
    resources: ResourceValidation
    is_valid: bool 