from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
from datetime import date

class SubmissionType(str, Enum):
    ABSTRACT = "ABSTRACT"          # zero-day milestone
    PAPER    = "PAPER"             # spans draft window

class ConferenceType(str, Enum):
    ENGINEERING = "ENGINEERING"
    MEDICAL     = "MEDICAL"

@dataclass
class Conference:
    id: str
    conf_type: ConferenceType
    recurrence: str                         # "annual" | "biennial"
    deadlines: Dict[SubmissionType, date]   # CFP dates per kind

@dataclass
class Submission:
    id: str
    kind: SubmissionType
    title: str

    # new, unambiguous
    earliest_start_date: date               # mods: PCCP/FDA ready; papers: data-ready

    conference_id: Optional[str]            # None → internal-only
    min_draft_window_days: Optional[int] = None  # drafting span

    engineering: bool
    depends_on: List[str]

    free_slack_days: int = 0
    penalty_cost_per_day: float = 0.0

@dataclass
class Config:
    default_lead_time_days: int
    max_concurrent_submissions: int
    slack_window_days: int
    conferences: List[Conference]
    submissions: List[Submission]
    data_files: Dict[str, str]
