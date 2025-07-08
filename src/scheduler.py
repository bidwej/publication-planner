from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
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

def greedy_schedule(cfg: Config) -> Dict[str, int]:
    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    months, month_idx = _build_calendar(cfg, sub_map)
    topo = _topological_order(sub_map)

    schedule: Dict[str, int] = {}
    active: Set[str] = set()

    for t in range(len(months)):
        # retire finished rows
        active = {
            sid for sid in active
            if t < schedule[sid] + _days_to_months(sub_map[sid].min_draft_window_days)
        }

        # rows whose deps are satisfied
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
                    schedule[d] + _days_to_months(sub_map[d].min_draft_window_days)
                    for d in s.depends_on
                ) if s.depends_on else 0,
            )

            if t < earliest:
                continue

            if s.external_due_date:
                finish = t + _days_to_months(s.min_draft_window_days)
                due_m = month_idx[(s.external_due_date.year, s.external_due_date.month)]
                if finish > due_m:
                    continue

            schedule[sid] = t
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

    if len(schedule) != len(sub_map):
        raise RuntimeError("Greedy scheduler could not place every row.")

    return schedule

def integer_schedule(cfg: Config) -> Dict[str, int]:
    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    _, month_idx = _build_calendar(cfg, sub_map)
    ids = list(sub_map)
    n = len(ids)

    c = np.ones(n)
    A, b = [], []

    for i, sid in enumerate(ids):
        for dep in sub_map[sid].depends_on:
            j = ids.index(dep)
            row = np.zeros(n)
            row[i] = -1
            row[j] = 1
            A.append(row)
            b.append(-_days_to_months(sub_map[dep].min_draft_window_days))

    for i, sid in enumerate(ids):
        ready_m = month_idx[(
            sub_map[sid].internal_ready_date.year,
            sub_map[sid].internal_ready_date.month
        )]
        row = np.zeros(n)
        row[i] = -1
        A.append(row)
        b.append(-ready_m)

    for i, sid in enumerate(ids):
        s = sub_map[sid]
        if s.external_due_date:
            due_m = month_idx[(
                s.external_due_date.year,
                s.external_due_date.month
            )]
            row = np.zeros(n)
            row[i] = 1
            A.append(row)
            b.append(due_m - _days_to_months(s.min_draft_window_days))

    res = scipy.optimize.linprog(
        c, A_ub=np.array(A), b_ub=np.array(b),
        bounds=[(0, None)] * n,
        method="highs"
    )
    if not res.success:
        raise RuntimeError("LP optimisation failed: " + res.message)

    fractional = {sid: float(res.x[i]) for i, sid in enumerate(ids)}
    integer_schedule = {k: int(round(v)) for k, v in fractional.items()}
    return integer_schedule

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
    # ** HERE IS THE CHANGE **
    end = max(dates) + relativedelta(days=cfg.default_lead_time_days)

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
        if conf.conf_type == ConferenceType.ENGINEERING and not s.engineering:
            raise ValueError(
                f"Medical submission {s.id} cannot target engineering venue {conf.id}"
            )


def _validate_structures(sub_map: Dict[str, Submission]) -> None:
    for s in sub_map.values():
        if s.kind == SubmissionType.ABSTRACT and s.min_draft_window_days != 0:
            raise ValueError(
                f"Abstract {s.id} must have min_draft_window_days == 0"
            )
        if (
            s.kind == SubmissionType.PAPER
            and not s.id.startswith("mod")
            and (s.min_draft_window_days is None or s.min_draft_window_days <= 0)
        ):
            raise ValueError(
                f"Paper {s.id} must have min_draft_window_days > 0 (got {s.min_draft_window_days})"
            )

def _days_to_months(days: Optional[int]) -> float:
    if days is None:
        return 0.0
    return days / 30.0

def load_schedule(path: str) -> dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {row["id"]: row["start_month_index"] for row in rows}

def save_schedule(
    schedule: dict[str, int],
    submissions: list[Submission],
    path: str
) -> None:
    output = []
    for sid, start_idx in schedule.items():
        s = next(sub for sub in submissions if sub.id == sid)
        output_row = {
            "id": s.id,
            "title": s.title,
            "kind": s.kind.value,
            "internal_ready_date": s.internal_ready_date.isoformat(),
            "external_due_date": s.external_due_date.isoformat() if s.external_due_date else None,
            "conference_id": s.conference_id,
            "min_draft_window_days": s.min_draft_window_days,
            "engineering": s.engineering,
            "depends_on": s.depends_on,
            "start_month_index": start_idx,
        }
        output.append(output_row)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Schedule saved to {path}")
