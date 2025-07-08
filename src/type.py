from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import date

class SubmissionType(str, Enum):
    ABSTRACT = "abstract"    # zero-day milestone
    PAPER    = "paper"       # spans min_draft_window_days

class ConferenceType(str, Enum):
    ENGINEERING = "ENGINEERING"
    MEDICAL     = "MEDICAL"

@dataclass
class Conference:
    id: str
    conf_type: ConferenceType                 # Eng / Med
    recurrence: str                           # "annual" | "biennial"
    deadlines: Dict[SubmissionType, date]     # e.g. {"abstract": ..., "paper": ...}

@dataclass
class Submission:
    id: str
    kind: SubmissionType
    title: str

    internal_ready_date: date                 # PCCP / FDA target date
    external_due_date: Optional[date]         # CFP deadline (or None)
    conference_id: Optional[str]              # None → internal-only

    min_draft_window_days: Optional[int] = None  # minimum drafting time in days

    engineering: bool                         # venue compatibility
    depends_on: List[str]                     # other Submission IDs

    free_slack_days: int = 0                  # allowed slip vs ready date (in days)
    penalty_cost_per_day: float = 0.0         # cost per day once past slack

@dataclass
class Config:
    default_lead_time_days: int               # how far into the future to extend the calendar
    max_concurrent_submissions: int           # maximum simultaneous active submissions
    slack_window_days: int                    # default mod slack (in days)

    conferences: List[Conference]
    submissions: List[Submission]

    data_files: Dict[str, str]                # JSON file paths
