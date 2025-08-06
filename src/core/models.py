"""Core data types and models."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date
from dataclasses import dataclass
from enum import Enum

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
    
    # Computed properties
    @property
    def submissions_dict(self) -> Dict[str, Submission]:
        return {sub.id: sub for sub in self.submissions}
    
    @property
    def conferences_dict(self) -> Dict[str, Conference]:
        return {conf.id: conf for conf in self.conferences}

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