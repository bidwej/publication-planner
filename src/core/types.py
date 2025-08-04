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
    depends_on: List[str]
    penalty_cost_per_day: Optional[float] = None

@dataclass
class Conference:
    """A conference with deadlines."""
    id: str
    name: str
    deadlines: Dict[SubmissionType, date]

@dataclass
class Config:
    """Configuration for the scheduler."""
    submissions: List[Submission]
    conferences: List[Conference]
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    penalty_costs: Optional[Dict[str, float]] = None
    
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
class DeadlineViolation(ConstraintViolation):
    """A deadline violation."""
    submission_title: str
    conference_id: str
    submission_type: str
    deadline: date
    end_date: date
    days_late: int

@dataclass
class DependencyViolation(ConstraintViolation):
    """A dependency violation."""
    dependency_id: str
    issue: str  # "missing_dependency", "invalid_dependency", "timing_violation"
    days_violation: Optional[int] = None

@dataclass
class ResourceViolation(ConstraintViolation):
    """A resource constraint violation."""
    date: date
    load: int
    limit: int
    excess: int

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

@dataclass
class ScheduleAnalysis:
    """Analysis of schedule completeness."""
    scheduled_count: int
    total_count: int
    completion_rate: float
    missing_submissions: List[Dict[str, Any]]

@dataclass
class ScheduleDistribution:
    """Distribution of submissions over time."""
    monthly_distribution: Dict[str, int]
    quarterly_distribution: Dict[str, int]
    yearly_distribution: Dict[str, int]

@dataclass
class SubmissionTypeAnalysis:
    """Analysis of submission types."""
    type_counts: Dict[str, int]
    type_percentages: Dict[str, float] 