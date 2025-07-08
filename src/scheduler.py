# src/scheduler.py
from __future__ import annotations

from typing import Dict, List, Set, Tuple
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import numpy as np
import scipy.optimize

from src.type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
    Conference
)

# -------------------------------------------------------------------- #
# GREEDY SCHEDULER  (integer, guaranteed feasible)                     #
# -------------------------------------------------------------------- #
def greedy_schedule(cfg: Config) -> Dict[str, int]:
    """
    Returns a dict {submission_id -> month_index} that respects:
        • dependencies
        • internal-ready dates
        • conference deadlines
        • venue compatibility
        • max_concurrent_submissions
    """
    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    months, month_idx = _build_calendar(cfg, sub_map)
    topo = _topological_order(sub_map)

    schedule: Dict[str, int] = {}
    active: Set[str] = set()

    for t in range(len(months)):
        # retire finished rows ----------------------------------------
        active = {
            sid for sid in active
            if t < schedule[sid] + sub_map[sid].draft_window_months
        }

        # rows whose deps are satisfied -------------------------------
        ready = [
            sid for sid in topo
            if sid not in schedule
            and all(dep in schedule for dep in sub_map[sid].depends_on)
        ]

        for sid in ready:
            if len(active) >= cfg.max_concurrent_submissions:
                break

            s = sub_map[sid]
            earliest = max(
                month_idx[(s.internal_ready_date.year, s.internal_ready_date.month)],
                max(
                    (schedule[d] + sub_map[d].draft_window_months)
                    for d in s.depends_on
                ) if s.depends_on else 0,
            )

            if t < earliest:
                continue

            # deadline check -----------------------------------------
            if s.external_due_date:
                finish = t + s.draft_window_months
                if finish > month_idx[(s.external_due_date.year, s.external_due_date.month)]:
                    continue

            schedule[sid] = t
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

    if len(schedule) != len(sub_map):
        raise RuntimeError("Greedy scheduler could not place every row.")

    return schedule

# -------------------------------------------------------------------- #
# LP RELAXATION  (fractional, best-effort)                             #
# -------------------------------------------------------------------- #
def integer_schedule(cfg: Config) -> Dict[str, int]:
    """
    LP relaxation using scipy.optimize.linprog.
    Returns integer start-month indices for each submission.
    """
    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    _, month_idx = _build_calendar(cfg, sub_map)
    ids = list(sub_map)
    n   = len(ids)

    # objective: minimise Σ start_month_i
    c = np.ones(n)

    A, b = [], []

    # deps -------------------------------------------------------------
    for i, sid in enumerate(ids):
        for dep in sub_map[sid].depends_on:
            j = ids.index(dep)
            row = np.zeros(n)
            row[i] = -1
            row[j] = 1
            A.append(row)
            b.append(-sub_map[dep].draft_window_months)

    # internal ready ---------------------------------------------------
    for i, sid in enumerate(ids):
        ready_m = month_idx[(sub_map[sid].internal_ready_date.year,
                             sub_map[sid].internal_ready_date.month)]
        row = np.zeros(n)
        row[i] = -1
        A.append(row)
        b.append(-ready_m)

    # external deadline ------------------------------------------------
    for i, sid in enumerate(ids):
        s = sub_map[sid]
        if s.external_due_date:
            due_m = month_idx[(s.external_due_date.year,
                               s.external_due_date.month)]
            row = np.zeros(n)
            row[i] = 1
            A.append(row)
            b.append(due_m - s.draft_window_months)

    res = scipy.optimize.linprog(
        c, A_ub=np.array(A), b_ub=np.array(b),
        bounds=[(0, None)] * n,
        method="highs"
    )
    if not res.success:
        raise RuntimeError("LP optimisation failed: " + res.message)

    fractional = {sid: float(res.x[i]) for i, sid in enumerate(ids)}
    # round to int month indices
    integer_schedule = {k: int(round(v)) for k, v in fractional.items()}
    return integer_schedule


# -------------------------------------------------------------------- #
# Shared helpers                                                       #
# -------------------------------------------------------------------- #
def _build_calendar(
    cfg: Config,
    sub_map: Dict[str, Submission]
) -> Tuple[List[datetime], Dict[Tuple[int, int], int]]:
    dates: List[date] = []
    for s in sub_map.values():
        dates.append(s.internal_ready_date)
        if s.external_due_date:
            dates.append(s.external_due_date)

    start = min(dates)
    end   = max(dates) + relativedelta(months=cfg.default_lead_time_months)

    months: List[datetime] = []
    cur = datetime(start.year, start.month, 1)
    while cur.date() <= end:
        months.append(cur)
        cur += relativedelta(months=1)

    idx = {(m.year, m.month): i for i, m in enumerate(months)}
    return months, idx


def _topological_order(sub_map: Dict[str, Submission]) -> List[str]:
    indeg = {sid: 0 for sid in sub_map}
    for s in sub_map.values():
        for _ in s.depends_on:
            indeg[s.id] += 1

    queue = [sid for sid, v in indeg.items() if v == 0]
    order: List[str] = []

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
    conf_map: Dict[str, Conference]
) -> None:
    for s in sub_map.values():
        if not s.conference_id:
            continue
        conf = conf_map[s.conference_id]
        if conf.conf_type == ConferenceType.MEDICAL and s.engineering:
            raise ValueError(
                f"Engineering submission {s.id} cannot target medical venue {conf.id}"
            )


def _validate_structures(sub_map: Dict[str, Submission]) -> None:
    """
    Lightweight structural checks that *use* SubmissionType.
    Ensures ABSTRACT rows have zero-duration and PAPER rows non-zero.
    """
    for s in sub_map.values():
        if s.kind == SubmissionType.ABSTRACT and s.draft_window_months != 0:
            raise ValueError(
                f"Abstract {s.id} must have draft_window_months == 0"
            )
        if s.kind == SubmissionType.PAPER and s.draft_window_months <= 0:
            raise ValueError(
                f"Paper {s.id} must have draft_window_months > 0"
            )

def load_schedule(path: str) -> dict[str, int]:
    """
    Load a previously saved schedule JSON into dict.
    """
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    return {row["id"]: row["start_month_index"] for row in rows}

def save_schedule(
    schedule: dict[str, int],
    submissions: list[Submission],
    path: str
) -> None:
    """
    Save the schedule + submission metadata to JSON.
    """
    output = []
    for sid, start_idx in schedule.items():
        s = next(sub for sub in submissions if sub.id == sid)
        output.append({
            "id": s.id,
            "title": s.title,
            "kind": s.kind.value,
            "internal_ready_date": s.internal_ready_date.isoformat(),
            "external_due_date": s.external_due_date.isoformat() if s.external_due_date else None,
            "conference_id": s.conference_id,
            "draft_window_months": s.draft_window_months,
            "engineering": s.engineering,
            "depends_on": s.depends_on,
            "start_month_index": start_idx,
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Schedule saved to {path}")
