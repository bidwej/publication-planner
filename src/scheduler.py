# src/scheduler.py

from __future__ import annotations
from typing import Dict, List, Set
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import numpy as np
import scipy.optimize

from src.type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
)

def greedy_schedule(cfg: Config) -> Dict[str, int]:
    """
    Greedy scheduler.
    Returns:
        Dict {submission_id -> month_index (int)}
    """
    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    months, month_index = _build_calendar(cfg, sub_map)

    topo = _topological_order(sub_map)

    schedule: Dict[str, int] = {}
    active: Set[str] = set()

    for t in range(len(months)):
        # retire finished rows
        for sid in list(active):
            s = sub_map[sid]
            if t >= schedule[sid] + s.draft_window_months:
                active.remove(sid)

        # enqueue rows whose deps are all satisfied
        ready = [
            sid for sid in topo
            if sid not in schedule
            and all(dep in schedule for dep in sub_map[sid].depends_on)
        ]

        for sid in ready:
            if len(active) >= cfg.max_concurrent_submissions:
                break

            earliest = max(
                month_index[(sub_map[sid].internal_ready_date.year, sub_map[sid].internal_ready_date.month)],
                max(
                    (schedule[d] + sub_map[d].draft_window_months)
                    for d in sub_map[sid].depends_on
                ) if sub_map[sid].depends_on else 0,
            )

            if t < earliest:
                continue

            ext = sub_map[sid].external_due_date
            if ext is not None:
                finish = t + sub_map[sid].draft_window_months
                if finish > month_index[(ext.year, ext.month)]:
                    continue  # would miss deadline

            schedule[sid] = t
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

    if len(schedule) != len(sub_map):
        raise RuntimeError("Greedy scheduler could not place every row.")

    return schedule


def solve_lp(cfg: Config) -> Dict[str, float]:
    """
    Attempts LP relaxation via scipy.optimize.linprog
    Returns:
        Dict {submission_id -> fractional month index}
    """

    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    months, month_index = _build_calendar(cfg, sub_map)

    submission_ids = list(sub_map.keys())
    n = len(submission_ids)

    c = np.ones(n)  # Minimize sum of start times

    A = []
    b = []

    # Dependencies
    for i, sid in enumerate(submission_ids):
        s = sub_map[sid]
        for dep in s.depends_on:
            j = submission_ids.index(dep)
            row = np.zeros(n)
            row[i] = -1
            row[j] = 1
            A.append(row)
            b.append(-sub_map[dep].draft_window_months)

    # Internal ready times
    for i, sid in enumerate(submission_ids):
        s = sub_map[sid]
        ready_month = month_index[(s.internal_ready_date.year, s.internal_ready_date.month)]
        row = np.zeros(n)
        row[i] = -1
        A.append(row)
        b.append(-ready_month)

    # External deadlines
    for i, sid in enumerate(submission_ids):
        s = sub_map[sid]
        if s.external_due_date:
            due_month = month_index[(s.external_due_date.year, s.external_due_date.month)]
            row = np.zeros(n)
            row[i] = 1
            A.append(row)
            b.append(due_month - s.draft_window_months)

    res = scipy.optimize.linprog(
        c,
        A_ub=np.array(A),
        b_ub=np.array(b),
        bounds=[(0, None)] * n,
        method="highs"
    )

    if not res.success:
        raise RuntimeError("LP optimization failed")

    return {
        sid: res.x[i] for i, sid in enumerate(submission_ids)
    }


# ----------------- Shared helpers -----------------------

def _build_calendar(cfg: Config, sub_map: Dict[str, Submission]) -> Tuple[List[datetime], Dict[Tuple[int, int], int]]:
    """
    Build the month grid from earliest internal_ready to latest external deadline.
    """
    all_dates: List[date] = []
    for s in sub_map.values():
        all_dates.append(s.internal_ready_date)
        if s.external_due_date:
            all_dates.append(s.external_due_date)

    start = min(all_dates)
    end   = max(all_dates)
    end = end + relativedelta(months=cfg.default_lead_time_months)

    months: List[datetime] = []
    cur = datetime(start.year, start.month, 1)
    while cur.date() <= end:
        months.append(cur)
        cur += relativedelta(months=1)

    month_index = {
        (m.year, m.month): idx for idx, m in enumerate(months)
    }

    return months, month_index


def _topological_order(sub_map: Dict[str, Submission]) -> List[str]:
    indeg = {sid: 0 for sid in sub_map}
    for s in sub_map.values():
        for d in s.depends_on:
            indeg[s.id] += 1

    queue = [sid for sid, k in indeg.items() if k == 0]
    order = []
    while queue:
        sid = queue.pop(0)
        order.append(sid)
        for s2 in sub_map.values():
            if sid in s2.depends_on:
                indeg[s2.id] -= 1
                if indeg[s2.id] == 0:
                    queue.append(s2.id)

    if len(order) != len(sub_map):
        raise RuntimeError("Dependency cycle detected")

    return order
