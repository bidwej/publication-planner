from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set, Tuple

from dateutil.relativedelta import relativedelta

from src.type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
    Conference,
)

# ───────────────────────────────
# Greedy scheduler
# ───────────────────────────────
def greedy_schedule(cfg: Config) -> Dict[str, date]:
    """
    Daily-based greedy scheduler.
    Returns:
      {submission_id → start_date}
    """
    sub_map = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_venue_compatibility(sub_map, conf_map)

    # Find time window
    dates = [s.earliest_start_date for s in sub_map.values()]
    for c in conf_map.values():
        dates.extend(c.deadlines.values())
    start_date = min(dates)
    end_date = max(dates) + timedelta(days=cfg.min_paper_lead_time_days)

    # Build topological order
    topo_order = _topological_order(sub_map)

    schedule: Dict[str, date] = {}
    active: Set[str] = set()

    current_date = start_date
    while current_date <= end_date:
        # Retire finished rows
        active = {
            sid
            for sid in active
            if current_date < schedule[sid] + timedelta(days=_draft_days(sub_map[sid], cfg))
        }

        # Find ready submissions
        ready = [
            sid for sid in topo_order
            if sid not in schedule
            and all(
                current_date >= schedule[dep] + timedelta(days=_draft_days(sub_map[dep], cfg))
                for dep in sub_map[sid].depends_on
            )
            and current_date >= sub_map[sid].earliest_start_date
        ]

        for sid in ready:
            if len(active) >= cfg.max_concurrent_submissions:
                break

            s = sub_map[sid]

            # Check conference deadline
            if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
                deadline = conf_map[s.conference_id].deadlines[s.kind]
                finish_date = current_date + timedelta(days=_draft_days(s, cfg)) - timedelta(days=1)
                if finish_date > deadline:
                    continue

            schedule[sid] = current_date
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

        current_date += timedelta(days=1)

    if len(schedule) != len(sub_map):
        missing = [sid for sid in sub_map if sid not in schedule]
        raise RuntimeError(f"Could not schedule submissions: {missing}")

    return schedule


# ───────────────────────────────
# Helpers
# ───────────────────────────────
def _draft_days(sub: Submission, cfg: Config) -> int:
    return (
        cfg.min_abstract_lead_time_days
        if sub.kind == SubmissionType.ABSTRACT
        else cfg.min_paper_lead_time_days
    )


def _topological_order(sub_map: Dict[str, Submission]) -> List[str]:
    """
    Return submission IDs in topological order.
    Raises RuntimeError if cyclic dependencies exist.
    """
    indeg = {sid: 0 for sid in sub_map}
    for s in sub_map.values():
        for _ in s.depends_on:
            indeg[s.id] += 1

    queue = [sid for sid, deg in indeg.items() if deg == 0]
    order = []

    while queue:
        sid = queue.pop(0)
        order.append(sid)
        for s in sub_map.values():
            if sid in s.depends_on:
                indeg[s.id] -= 1
                if indeg[s.id] == 0:
                    queue.append(s.id)

    if len(order) != len(sub_map):
        raise RuntimeError("Dependency cycle detected")
    return order


def _validate_venue_compatibility(
    sub_map: Dict[str, Submission],
    conf_map: Dict[str, Conference],
) -> None:
    for s in sub_map.values():
        if not s.conference_id:
            continue
        conf = conf_map[s.conference_id]
        if conf.conf_type == ConferenceType.ENGINEERING and not s.engineering:
            raise ValueError(
                f"Medical submission {s.id} cannot target engineering venue {conf.id}"
            )


# ───────────────────────────────
# Persistence helpers
# ───────────────────────────────
def load_schedule(path: str) -> Dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {row["id"]: row["start_month_index"] for row in rows}


def save_schedule(
    schedule: Dict[str, date],
    submissions: List[Submission],
    path: str,
) -> None:
    rows = []
    for sid, start_date in schedule.items():
        s = next(sub for sub in submissions if sub.id == sid)
        rows.append({
            "id": s.id,
            "title": s.title,
            "kind": s.kind.value,
            "earliest_start_date": s.earliest_start_date.isoformat(),
            "conference_id": s.conference_id,
            "engineering": s.engineering,
            "depends_on": s.depends_on,
            "start_date": start_date.isoformat(),
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"Schedule saved to {path}")
