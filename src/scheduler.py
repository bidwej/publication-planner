from __future__ import annotations

import json
from datetime import datetime, date
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
def greedy_schedule(cfg: Config) -> Dict[str, int]:
    """
    Returns {submission_id → start_month_index} using a greedy heuristic.
    Draft length per task:
        ABSTRACT → cfg.min_abstract_lead_time_days
        PAPER    → cfg.min_paper_lead_time_days
    """
    sub_map = {s.id: s for s in cfg.submissions}
    conf_map = {c.id: c for c in cfg.conferences}

    _validate_structures(sub_map)
    _validate_venue_compatibility(sub_map, conf_map)

    months, month_idx = _build_calendar(cfg, sub_map, conf_map)
    topo = _topological_order(sub_map)

    schedule: Dict[str, int] = {}
    active: Set[str] = set()

    for t in range(len(months)):
        # Retire finished rows
        active = {
            sid
            for sid in active
            if t < schedule[sid] + _days_to_months(_draft_days(sub_map[sid], cfg))
        }

        # Ready submissions whose deps are done
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
                    schedule[d] + _days_to_months(_draft_days(sub_map[d], cfg))
                    for d in s.depends_on
                ) if s.depends_on else 0,
            )
            if t < earliest:
                continue

            # Conference deadline check
            if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
                due = conf_map[s.conference_id].deadlines[s.kind]
                finish = t + _days_to_months(_draft_days(s, cfg))
                if finish > month_idx[(due.year, due.month)]:
                    continue

            schedule[sid] = t
            active.add(sid)

        if len(schedule) == len(sub_map):
            break

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


def _build_calendar(
    cfg: Config,
    sub_map: Dict[str, Submission],
    conf_map: Dict[str, Conference],
) -> Tuple[List[datetime], Dict[Tuple[int, int], int]]:
    dates: List[date] = []

    for s in sub_map.values():
        dates.append(s.earliest_start_date)
        if s.conference_id and s.kind in conf_map[s.conference_id].deadlines:
            dates.append(conf_map[s.conference_id].deadlines[s.kind])

    start = min(dates)
    end = max(dates) + relativedelta(days=cfg.min_paper_lead_time_days)

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

    q = [sid for sid, v in indeg.items() if v == 0]
    order: List[str] = []
    while q:
        sid = q.pop(0)
        order.append(sid)
        for s in sub_map.values():
            if sid in s.depends_on:
                indeg[s.id] -= 1
                if indeg[s.id] == 0:
                    q.append(s.id)

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


def _validate_structures(sub_map: Dict[str, Submission]) -> None:
    for s in sub_map.values():
        if s.kind == SubmissionType.ABSTRACT and _draft_days(s, cfg=None) != 0:
            # always zero by definition, check left for completeness
            continue
        if s.kind == SubmissionType.PAPER and not s.id.startswith("mod"):
            # nothing else to validate now that draft length is global
            continue


def _days_to_months(days: int) -> float:
    return days / 30.0


# ───────────────────────────────
# Persistence helpers
# ───────────────────────────────
def load_schedule(path: str) -> Dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {r["id"]: r["start_month_index"] for r in rows}


def save_schedule(
    schedule: Dict[str, int],
    submissions: List[Submission],
    path: str,
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
                "engineering": s.engineering,
                "depends_on": s.depends_on,
                "start_month_index": start_idx,
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"Schedule saved to {path}")
