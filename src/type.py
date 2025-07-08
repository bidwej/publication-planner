from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import date

class SubmissionType(str, Enum):
    """Two flavours of work we actually submit to a venue."""
    ABSTRACT = "abstract"   # zero-month point milestone
    PAPER    = "paper"      # spans draft_window_months

class ConferenceType(str, Enum):
    ENGINEERING = "Engineering"
    MEDICAL     = "Medical"

@dataclass
class Conference:
    """External venue; may expose one or two deadlines."""
    id: str
    conf_type: ConferenceType                 # Eng / Med
    recurrence: str                           # "annual" | "biennial"
    deadlines: Dict[SubmissionType, date]     # {"abstract": ..., "paper": ...}

@dataclass
class Submission:
    """
    **Single-table row** – covers:
    • PCCP engineering milestones (internal_ready_date)
    • conference abstracts
    • conference papers
    """
    id: str
    kind: SubmissionType
    title: str

    internal_ready_date: date                 # PCCP / FDA target
    external_due_date: Optional[date]         # CFP deadline (or None)
    conference_id: Optional[str]              # None → internal only
    draft_window_months: int                  # 0 for abstracts

    engineering: bool                         # venue compatibility
    depends_on: List[str]                     # other Submission IDs

    free_slack_months: int = 0                # allowed slip vs ready date
    penalty_cost_per_month: int = 0           # cost once past slack

@dataclass
class Config:
    default_lead_time_months: int
    max_concurrent_submissions: int
    slack_window_days: int

    conferences: List[Conference]
    submissions: List[Submission]

    data_files: Dict[str, str]
