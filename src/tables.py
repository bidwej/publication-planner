from __future__ import annotations
from datetime import datetime
from typing import Dict, List

from src.type import SubmissionType
from src.scheduler import _days_to_months
from planner import Planner

def generate_monthly_table(
    planner: Planner,
    schedule: Dict[str, int]
) -> List[Dict[str, str]]:
    # Generates a monthly table showing active submissions and deadlines
    rows: List[Dict[str, str]] = []

    for i, month in enumerate(planner.months):
        active = []
        for sid, start_idx in schedule.items():
            s = planner.sub_map[sid]

            # Compute how many months the submission occupies
            duration_months = _days_to_months(s.min_draft_window_days)

            if start_idx <= i < start_idx + duration_months:
                active.append(sid)

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
