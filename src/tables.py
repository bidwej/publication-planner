# src/tables.py

from __future__ import annotations
from datetime import datetime
from typing import Dict, List

from type import SubmissionType
from planner import Planner

def generate_monthly_table(
    planner: Planner,
    schedule: Dict[str, int]
) -> List[Dict[str, str]]:
    """
    Generates a monthly table showing active submissions
    and deadlines for all conferences.

    Parameters
    ----------
    planner : Planner
        A Planner instance with timeline info.
    schedule : Dict[str, int]
        A dict of submission_id → start month index.

    Returns
    -------
    List[Dict[str, str]]
        Each dict contains "Month", "Active Submissions", "Deadlines"
    """
    rows: List[Dict[str, str]] = []

    for i, month in enumerate(planner.months):
        active = []
        for sid, start_idx in schedule.items():
            s = planner.sub_map[sid]
            if start_idx <= i < start_idx + s.draft_window_months:
                active.append(sid)

        # Find deadlines in this month
        deadlines = []
        for conf in planner.conf_map.values():
            for kind, d in conf.deadlines.items():
                if d.year == month.year and d.month == month.month:
                    deadlines.append(f"{conf.id} {kind.value} {d.isoformat()}")

        rows.append({
            "Month": month.strftime("%Y-%m"),
            "Active Submissions": ", ".join(sorted(active)),
            "Deadlines": "; ".join(sorted(deadlines)),
        })

    return rows
