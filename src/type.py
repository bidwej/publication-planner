from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import date

class SubmissionType(str, Enum):
    ABSTRACT = "ABSTRACT"  # zero-day milestone
    PAPER = "PAPER"  # spans a draft window

class ConferenceType(str, Enum):
    ENGINEERING = "ENGINEERING"
    MEDICAL = "MEDICAL"

@dataclass
class Conference:
    id: str
    conf_type: ConferenceType
    recurrence: str  # "annual" | "biennial"
    deadlines: Dict[SubmissionType, date]  # CFP dates per kind

@dataclass
class Submission:
    id: str
    kind: SubmissionType
    title: str
    earliest_start_date: date  # PCCP/FDA ready OR data-ready
    conference_id: Optional[str]  # None → internal-only
    engineering: bool
    depends_on: List[str]
    penalty_cost_per_day: float = 0.0  # optional cost model

@dataclass
class Config:
    min_abstract_lead_time_days: int  # default lead time for abstracts
    min_paper_lead_time_days: int  # default lead time for papers
    max_concurrent_submissions: int
    mod_to_paper_gap_days: int
    conferences: List[Conference]
    submissions: List[Submission]
    data_files: Dict[str, str]
    # New fields for enhanced scheduling
    paper_parent_gap_days: int = 90  # gap between parent and child papers
    priority_weights: Optional[Dict[str, float]] = None
    penalty_costs: Optional[Dict[str, float]] = None
    scheduling_options: Optional[Dict[str, Any]] = None
    blackout_dates: Optional[List[date]] = None  # computed from blackout.json