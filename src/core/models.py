"""Core data types and models."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from datetime import date, timedelta
from dataclasses import asdict, dataclass
from enum import Enum
from dateutil.parser import parse as parse_date

from src.core.constants import SCHEDULING_CONSTANTS

class SubmissionType(str, Enum):
    """Types of submissions."""
    PAPER = "paper"
    ABSTRACT = "abstract"
    POSTER = "poster"

class ConferenceSubmissionType(str, Enum):
    """Types of conference submission requirements."""
    ABSTRACT_ONLY = "abstract_only"      # Only accepts abstracts
    PAPER_ONLY = "paper_only"           # Only accepts papers
    POSTER_ONLY = "poster_only"         # Only accepts posters
    ABSTRACT_AND_PAPER = "abstract_and_paper"  # Requires abstract before paper
    ABSTRACT_OR_PAPER = "abstract_or_paper"    # Accepts either abstract or paper
    ALL_TYPES = "all_types"             # Accepts all submission types

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

@dataclass
class Submission:
    """A submission to a conference."""
    id: str
    title: str
    kind: SubmissionType
    conference_id: Optional[str] = None  # Optional - None for work items
    depends_on: Optional[List[str]] = None
    draft_window_months: int = 3
    lead_time_from_parents: int = 0
    penalty_cost_per_day: Optional[float] = None
    engineering: bool = False
    earliest_start_date: Optional[date] = None
    candidate_conferences: Optional[List[str]] = None  # Suggested conferences
    
    # Additional fields to handle data structure mismatches
    mod_dependencies: Optional[List[int]] = None  # For papers that depend on mods
    parent_papers: Optional[List[str]] = None  # For papers that depend on other papers
    est_data_ready: Optional[date] = None  # For mods - estimated data ready date
    free_slack_months: Optional[int] = None  # For mods - free slack time
    penalty_cost_per_month: Optional[float] = None  # For mods - monthly penalty cost
    next_mod: Optional[int] = None  # For mods - next mod in sequence
    phase: Optional[int] = None  # For mods - development phase
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.candidate_conferences is None:
            self.candidate_conferences = []
        if self.mod_dependencies is None:
            self.mod_dependencies = []
        if self.parent_papers is None:
            self.parent_papers = []
    
    def validate(self) -> List[str]:
        """Validate submission and return list of errors."""
        errors = []
        if not self.id:
            errors.append("Missing submission ID")
        if not self.title:
            errors.append("Missing title")
        # Conference ID is optional for work items (mods)
        # Papers can have conference_id or candidate_conferences
        if self.kind == SubmissionType.PAPER and not self.conference_id and not self.candidate_conferences:
            errors.append("Papers must have either conference_id or candidate_conferences")
        if self.draft_window_months < 0:
            errors.append("Draft window months cannot be negative")
        if self.lead_time_from_parents < 0:
            errors.append("Lead time from parents cannot be negative")
        if self.penalty_cost_per_day is not None and self.penalty_cost_per_day < 0:
            errors.append("Penalty cost per day cannot be negative")
        if self.penalty_cost_per_month is not None and self.penalty_cost_per_month < 0:
            errors.append("Penalty cost per month cannot be negative")
        if self.free_slack_months is not None and self.free_slack_months < 0:
            errors.append("Free slack months cannot be negative")
        if self.phase is not None and self.phase < 1:
            errors.append("Phase must be at least 1")
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
        # Fixed time constants
        days_per_month = 30
        
        if self.kind == SubmissionType.ABSTRACT:
            # Work items (abstracts) should have meaningful duration for timeline visibility
            # Use configurable work item duration, default to 14 days if not specified
            work_item_duration = getattr(config, 'work_item_duration_days', 14)
            return work_item_duration
        if self.kind == SubmissionType.POSTER:
            # Posters typically have shorter duration than papers
            if self.draft_window_months > 0:
                return self.draft_window_months * days_per_month
            return SCHEDULING_CONSTANTS.poster_duration_days
        # SubmissionType.PAPER
        # Use draft_window_months if available, otherwise fall back to config
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

@dataclass
class Conference:
    """A conference with deadlines."""
    id: str
    name: str
    conf_type: ConferenceType
    recurrence: ConferenceRecurrence
    deadlines: Dict[SubmissionType, date]
    submission_types: Optional[ConferenceSubmissionType] = None  # What types of submissions are accepted
    
    def __post_init__(self):
        # Auto-determine submission type based on deadlines if not specified
        if self.submission_types is None:
            self.submission_types = self._determine_submission_type()
    
    def _determine_submission_type(self) -> ConferenceSubmissionType:
        """Determine submission type based on available deadlines."""
        has_abstract = SubmissionType.ABSTRACT in self.deadlines
        has_paper = SubmissionType.PAPER in self.deadlines
        has_poster = SubmissionType.POSTER in self.deadlines
        
        if has_abstract and has_paper:
            return ConferenceSubmissionType.ABSTRACT_AND_PAPER
        elif has_abstract and not has_paper:
            return ConferenceSubmissionType.ABSTRACT_ONLY
        elif has_paper and not has_abstract:
            return ConferenceSubmissionType.PAPER_ONLY
        elif has_poster and not has_abstract and not has_paper:
            return ConferenceSubmissionType.POSTER_ONLY
        elif has_abstract and has_paper and has_poster:
            return ConferenceSubmissionType.ALL_TYPES
        else:
            return ConferenceSubmissionType.ABSTRACT_OR_PAPER
    
    def accepts_submission_type(self, submission_type: SubmissionType) -> bool:
        """Check if conference accepts this submission type."""
        if self.submission_types == ConferenceSubmissionType.ALL_TYPES:
            return True
        elif self.submission_types == ConferenceSubmissionType.ABSTRACT_ONLY:
            return submission_type == SubmissionType.ABSTRACT
        elif self.submission_types == ConferenceSubmissionType.PAPER_ONLY:
            return submission_type == SubmissionType.PAPER
        elif self.submission_types == ConferenceSubmissionType.POSTER_ONLY:
            return submission_type == SubmissionType.POSTER
        elif self.submission_types == ConferenceSubmissionType.ABSTRACT_AND_PAPER:
            return submission_type in [SubmissionType.ABSTRACT, SubmissionType.PAPER]
        elif self.submission_types == ConferenceSubmissionType.ABSTRACT_OR_PAPER:
            return submission_type in [SubmissionType.ABSTRACT, SubmissionType.PAPER]
        return False
    
    def requires_abstract_before_paper(self) -> bool:
        """Check if conference requires abstract submission before paper submission."""
        return self.submission_types == ConferenceSubmissionType.ABSTRACT_AND_PAPER
    
    def get_required_dependencies(self, submission_type: SubmissionType) -> List[str]:
        """Get list of required dependencies for this submission type at this conference."""
        dependencies = []
        
        if submission_type == SubmissionType.PAPER and self.requires_abstract_before_paper():
            # For papers at conferences requiring abstracts, the abstract ID would be
            # generated based on the paper ID and conference ID
            # This is handled in the Config class during validation
            # Return empty list as this is handled at the submission level
            pass
        
        return dependencies
    
    def validate_submission_compatibility(self, submission: Submission) -> List[str]:
        """Validate that a submission is compatible with this conference."""
        errors = []
        
        # Check if conference accepts this submission type
        if not self.accepts_submission_type(submission.kind):
            errors.append(f"Conference {self.id} does not accept {submission.kind.value} submissions")
        
        # Check if submission has required dependencies
        if submission.kind == SubmissionType.PAPER and self.requires_abstract_before_paper():
            abstract_id = generate_abstract_id(submission.id, self.id)
            if abstract_id not in (submission.depends_on or []):
                errors.append(f"Paper {submission.id} must depend on abstract {abstract_id} for conference {self.id}")
        
        return errors
    
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


# Utility functions for abstract-paper dependencies
def generate_abstract_id(paper_id: str, conference_id: str) -> str:
    """Generate abstract ID for paper."""
    return f"{paper_id}-abs"  # Simplified, no conference in ID


def create_abstract_submission(paper: Submission, conference_id: str, 
                             penalty_costs: Dict[str, float]) -> Submission:
    """Create abstract submission as work item."""
    abstract_id = generate_abstract_id(paper.id, conference_id)
    
    return Submission(
        id=abstract_id,
        title=f"Abstract for {paper.title}",
        kind=SubmissionType.ABSTRACT,
        conference_id=None,  # Work item, no conference assignment
        depends_on=[],  # No dependencies
        draft_window_months=1,
        lead_time_from_parents=0,
        penalty_cost_per_day=penalty_costs.get("default_mod_penalty_per_day", 1000.0),
        engineering=paper.engineering,
        earliest_start_date=paper.earliest_start_date,
        candidate_conferences=[conference_id]  # Store as candidate
    )


def ensure_abstract_paper_dependency(paper: Submission, abstract_id: str) -> None:
    """Ensure a paper depends on its corresponding abstract."""
    if paper.depends_on is None:
        paper.depends_on = []
    
    if abstract_id not in paper.depends_on:
        paper.depends_on.append(abstract_id)


def find_abstract_for_paper(paper_id: str, conference_id: str, 
                          submissions_dict: Dict[str, Submission]) -> Optional[str]:
    """Find the abstract ID for a paper at a specific conference."""
    abstract_id = generate_abstract_id(paper_id, conference_id)
    return abstract_id if abstract_id in submissions_dict else None


@dataclass
class Config:
    """Configuration for the scheduler."""
    submissions: List[Submission]
    conferences: List[Conference]
    min_abstract_lead_time_days: int
    min_paper_lead_time_days: int
    max_concurrent_submissions: int
    default_paper_lead_time_months: int = 3
    work_item_duration_days: int = 14  # Duration for work items (abstracts)
    conference_response_time_days: int = 90
    max_backtrack_days: int = 30
    randomness_factor: float = 0.1
    lookahead_bonus_increment: float = 0.5
    penalty_costs: Optional[Dict[str, float]] = None
    priority_weights: Optional[Dict[str, float]] = None
    scheduling_options: Optional[Dict[str, Any]] = None
    blackout_dates: Optional[List[date]] = None
    data_files: Optional[Dict[str, str]] = None
    
    @classmethod
    def create_default(cls) -> 'Config':
        """Create a default configuration with minimal data for app initialization."""
        # Default penalty costs
        default_penalty_costs = {
            "default_mod_penalty_per_day": 1000.0,
            "default_paper_penalty_per_day": 2000.0
        }
        
        # Default priority weights
        default_priority_weights = {
            "engineering_paper": 2.0,
            "medical_paper": 1.0,
            "mod": 1.5,
            "abstract": 0.5
        }
        
        # Default scheduling options
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
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            default_paper_lead_time_months=3,
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
        
        # Validate abstract-paper dependencies
        errors.extend(self._validate_abstract_paper_dependencies())
        
        # Validate circular dependencies
        errors.extend(self._validate_circular_dependencies())
        
        # Validate missing dependencies
        errors.extend(self._validate_missing_dependencies())

        return errors

    def _validate_abstract_paper_dependencies(self) -> List[str]:
        """Validate that papers have required abstract dependencies."""
        errors = []
        submission_dict = {sub.id: sub for sub in self.submissions}
        conference_dict = {conf.id: conf for conf in self.conferences}

        for submission in self.submissions:
            if submission.kind == SubmissionType.PAPER and submission.conference_id:
                conference = conference_dict.get(submission.conference_id)
                if conference and conference.requires_abstract_before_paper():
                    # Check if required abstract exists using simplified format
                    base_paper_id = submission.id.split('-')[0]  # Get base paper ID
                    abstract_id = f"{base_paper_id}-abs"
                    if abstract_id not in submission_dict:
                        errors.append(f"Paper {submission.id} requires abstract {abstract_id} for conference {submission.conference_id}")
                    else:
                        # Check if paper depends on its abstract
                        abstract = submission_dict[abstract_id]
                        if abstract_id not in (submission.depends_on or []):
                            errors.append(f"Paper {submission.id} must depend on its abstract {abstract_id}")
                        # Check if abstract has the paper's conference as a candidate
                        if submission.conference_id not in (abstract.candidate_conferences or []):
                            errors.append(f"Abstract {abstract_id} must have conference {submission.conference_id} as candidate")

        return errors

    def _validate_circular_dependencies(self) -> List[str]:
        """Validate that there are no circular dependencies."""
        errors = []
        submission_dict = {sub.id: sub for sub in self.submissions}
        
        def has_circular_dependency(sub_id: str, visited: set, path: list) -> bool:
            """Check for circular dependencies using DFS."""
            if sub_id in visited:
                return sub_id in path
            
            visited.add(sub_id)
            path.append(sub_id)
            
            submission = submission_dict.get(sub_id)
            if not submission or not submission.depends_on:
                path.pop()
                return False
            
            for dep_id in submission.depends_on:
                if has_circular_dependency(dep_id, visited, path):
                    return True
            
            path.pop()
            return False
        
        # Check each submission for circular dependencies
        for submission in self.submissions:
            if has_circular_dependency(submission.id, set(), []):
                errors.append(f"Circular dependency detected involving submission {submission.id}")
        
        return errors

    def _validate_missing_dependencies(self) -> List[str]:
        """Validate that all dependencies exist."""
        errors = []
        submission_ids = {sub.id for sub in self.submissions}
        
        for submission in self.submissions:
            if submission.depends_on:
                for dep_id in submission.depends_on:
                    if dep_id not in submission_ids:
                        errors.append(f"Submission {submission.id} depends on non-existent submission {dep_id}")
        
        return errors
    
    def ensure_abstract_paper_dependencies(self) -> None:
        """Automatically create missing abstract submissions and dependencies."""
        if not self.submissions or not self.conferences:
            return
        
        submission_dict = {sub.id: sub for sub in self.submissions}
        conference_dict = {conf.id: conf for conf in self.conferences}
        penalty_costs = self.penalty_costs or {}
        
        # Find papers that need abstracts
        papers_needing_abstracts = []
        for submission in self.submissions:
            if (submission.kind == SubmissionType.PAPER and 
                submission.conference_id and 
                submission.conference_id in conference_dict):
                
                conference = conference_dict[submission.conference_id]
                if conference.requires_abstract_before_paper():
                    # Use simplified abstract ID format
                    base_paper_id = submission.id.split('-')[0]
                    abstract_id = f"{base_paper_id}-abs"
                    if abstract_id not in submission_dict:
                        papers_needing_abstracts.append((submission, abstract_id))
        
        # Create missing abstracts
        for paper, abstract_id in papers_needing_abstracts:
            abstract = create_abstract_submission(paper, paper.conference_id, penalty_costs)
            abstract.id = abstract_id  # Use simplified ID
            self.submissions.append(abstract)
            submission_dict[abstract_id] = abstract
            
            # Ensure paper depends on abstract
            ensure_abstract_paper_dependency(paper, abstract_id)
    
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
            return latest_deadline + timedelta(days=90)  # 3 months buffer after latest deadline
        else:
            return date.today() + timedelta(days=365)

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
    conference_compatibility_penalties: float
    abstract_paper_dependency_penalties: float

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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_submissions': self.total_submissions,
            'schedule_span': self.schedule_span,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'penalty_score': self.penalty_score,
            'quality_score': self.quality_score,
            'efficiency_score': self.efficiency_score,
            'deadline_compliance': self.deadline_compliance,
            'resource_utilization': self.resource_utilization
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleSummary':
        """Create from dictionary."""
        start_date = None
        end_date = None
        
        if data.get('start_date'):
            try:
                start_date = parse_date(data['start_date']).date()
            except (ValueError, TypeError):
                pass
                
        if data.get('end_date'):
            try:
                end_date = parse_date(data['end_date']).date()
            except (ValueError, TypeError):
                pass
        
        return cls(
            total_submissions=data.get('total_submissions', 0),
            schedule_span=data.get('schedule_span', 0),
            start_date=start_date,
            end_date=end_date,
            penalty_score=data.get('penalty_score', 0.0),
            quality_score=data.get('quality_score', 0.0),
            efficiency_score=data.get('efficiency_score', 0.0),
            deadline_compliance=data.get('deadline_compliance', 0.0),
            resource_utilization=data.get('resource_utilization', 0.0)
        )

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

@dataclass
class ScheduleState:
    """Complete state of a schedule for serialization."""
    schedule: Dict[str, date]
    config: Config
    strategy: SchedulerStrategy
    metadata: Dict[str, Any]
    timestamp: str
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Use asdict for config serialization
        config_dict = asdict(self.config)
        # Convert date objects to ISO format strings
        if config_dict.get("blackout_dates"):
            config_dict["blackout_dates"] = [d.isoformat() for d in config_dict["blackout_dates"]]
        
        return {
            "schedule": {k: v.isoformat() for k, v in self.schedule.items()},
            "config": config_dict,
            "strategy": self.strategy.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleState':
        """Create a ScheduleState from a dictionary."""
        # Parse schedule dates
        schedule = {}
        if "schedule" in data:
            for k, v in data["schedule"].items():
                try:
                    schedule[k] = parse_date(v).date()
                except (ValueError, TypeError):
                    continue
        
        # Parse blackout dates
        blackout_dates = []
        if "blackout_dates" in data:
            for d in data["blackout_dates"]:
                try:
                    blackout_dates.append(parse_date(d).date())
                except (ValueError, TypeError):
                    continue
        
        return cls(
            schedule=schedule,
            config=Config(
                submissions=[],  # Would need to reconstruct from data files
                conferences=[],  # Would need to reconstruct from data files
                min_abstract_lead_time_days=data.get("min_abstract_lead_time_days", 30),
                min_paper_lead_time_days=data.get("min_paper_lead_time_days", 90),
                max_concurrent_submissions=data.get("max_concurrent_submissions", 3),
                default_paper_lead_time_months=data.get("default_paper_lead_time_months", 3),
                penalty_costs=data.get("penalty_costs", {}),
                priority_weights=data.get("priority_weights", {}),
                scheduling_options=data.get("scheduling_options", {}),
                blackout_dates=blackout_dates,
                data_files=data.get("data_files", {})
            ),
            strategy=SchedulerStrategy(data.get("strategy", "greedy")),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", "1.0")
        )

 