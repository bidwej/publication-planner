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
    Conference,
)


# ──────────────────  Greedy scheduler  ──────────────────
def greedy_schedule(cfg: Config) -> Dict[str, int]:
    sub_map = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    months, month_idx = _build_calendar(cfg, sub_map, conf_map)
    topo = _topological_order(sub_map)

    schedule: Dict[str, int] = {}
    active: Set[str] = set()

    for t in range(len(months)):
        # retire finished rows
        active = {
            sid for sid in active
            if t < schedule[sid] + _days_to_months(sub_map[sid].min_draft_window_days)
        }

        # ready rows (deps satisfied)
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
                month_idx[(s.earliest_start_date.year, s.earliest_start_date.month)],
                max(
                    schedule[d] + _days_to_months(sub_map[d].min_draft_window_days)
                    for d in s.depends_on
                ) if s.depends_on else 0,
            )
            if t < earliest:
                continue

            # must finish before conference deadline (if any)
            if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
                due_date = conf_map[s.conference_id].deadlines[s.kind]
                finish = t + _days_to_months(s.min_draft_window_days)
                due_m = month_idx[(due_date.year, due_date.month)]
                if finish > due_m:
                    continue

            schedule[sid] = t
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

    if len(schedule) != len(sub_map):
        unplaced = [sid for sid in sub_map if sid not in schedule]
        print("DEBUG unplaced submissions:", unplaced)
        raise RuntimeError("Greedy scheduler could not place every row.")

    return schedule


# ──────────────────  Linear-program scheduler  ──────────────────
def integer_schedule(cfg: Config) -> Dict[str, int]:
    sub_map = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    months, month_idx = _build_calendar(cfg, sub_map, conf_map)
    ids = list(sub_map)
    n = len(ids)

    c = np.ones(n)  # minimise total start time
    A, b = [], []

    # dependency constraints
    for i, sid in enumerate(ids):
        for dep in sub_map[sid].depends_on:
            j = ids.index(dep)
            row = np.zeros(n)
            row[i] = -1
            row[j] = 1
            A.append(row)
            b.append(-_days_to_months(sub_map[dep].min_draft_window_days))

    # cannot start before earliest_start_date
    for i, sid in enumerate(ids):
        ready_m = month_idx[(
            sub_map[sid].earliest_start_date.year,
            sub_map[sid].earliest_start_date.month
        )]
        row = np.zeros(n)
        row[i] = -1
        A.append(row)
        b.append(-ready_m)

    # must finish before conference deadline (if any)
    for i, sid in enumerate(ids):
        s = sub_map[sid]
        if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
            due = conf_map[s.conference_id].deadlines[s.kind]
            due_m = month_idx[(due.year, due.month)]
            row = np.zeros(n)
            row[i] = 1
            A.append(row)
            b.append(due_m - _days_to_months(s.min_draft_window_days))

    res = scipy.optimize.linprog(
        c, A_ub=np.array(A), b_ub=np.array(b),
        bounds=[(0, None)] * n, method="highs"
    )
    if not res.success:
        raise RuntimeError("LP optimisation failed: " + res.message)

    return {ids[i]: int(round(v)) for i, v in enumerate(res.x)}


# ──────────────────  Helpers  ──────────────────
def _build_calendar(
    cfg: Config,
    sub_map: Dict[str, Submission],
    conf_map: Dict[str, Conference]
) -> Tuple[List[datetime], Dict[Tuple[int, int], int]]:
    """Return month list + lookup; calendar extends past latest deadline."""
    dates: List[date] = []

    for s in sub_map.values():
        dates.append(s.earliest_start_date)
        if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
            dates.append(conf_map[s.conference_id].deadlines[s.kind])

    start = min(dates)
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
            raise ValueError(f"{s.id}: abstracts must have draft_window == 0")
        if (
            s.kind == SubmissionType.PAPER
            and not s.id.startswith("mod")
            and (s.min_draft_window_days is None or s.min_draft_window_days <= 0)
        ):
            raise ValueError(f"{s.id}: papers need positive draft_window")


def _days_to_months(days: Optional[int]) -> float:
    return 0.0 if days is None else days / 30.0


# ── persistence helpers (unchanged except for renamed field) ─────────
def load_schedule(path: str) -> Dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {r["id"]: r["start_month_index"] for r in rows}


def save_schedule(
    schedule: Dict[str, int],
    submissions: List[Submission],
    path: str
) -> None:
    rows = []
    for sid, start_idx in schedule.items():
        s = next(sub for sub in submissions if sub.id == sid)
        rows.append(
            {
                "id": s.id,
                "title": s.title,
                "kind": s.kind.value,
                "earliest_start_date": s.earliest_start_date.isoformat(),
                "conference_id": s.conference_id,
                "min_draft_window_days": s.min_draft_window_days,
                "engineering": s.engineering,
                "depends_on": s.depends_on,
                "start_month_index": start_idx,
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"Schedule saved to {path}")
