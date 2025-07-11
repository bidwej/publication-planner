from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple

from dateutil.relativedelta import relativedelta

from src.type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
    Conference,
)

# --------------------------------------------------------------------------- #
# Public entry-point
# --------------------------------------------------------------------------- #
# TODO: See README.md
# def enhanced_greedy(cfg, iteration):
#     # Randomize priorities
#     noise = random.uniform(0.8, 1.2, size=n_items)
#     priority = base_priority * noise
    
#     # Add lookahead
#     def score_choice(item, date):
#         immediate = -penalty_cost[item] * delay
#         future = simulate_next_30_days(item, date)
#         return immediate + 0.5 * future
    
#     # Detect local minimum
#     if concurrency_utilization < 0.7 * max_concurrent:
#         increase_randomization()

def greedy_schedule(cfg: Config) -> Dict[str, date]:
    """
    Greedy daily scheduler for abstracts & papers.

    Returns
    -------
    dict
        {submission_id: start_date}
    """
    _auto_link_abstract_paper(cfg.submissions)

    sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
    conf_map: Dict[str, Conference] = {c.id: c for c in cfg.conferences}
    _validate_venue_compatibility(sub_map, conf_map)

    topo = _topological_order(sub_map)

    # global time window
    dates = [s.earliest_start_date for s in sub_map.values()]
    for c in conf_map.values():
        dates.extend(c.deadlines.values())
    current = min(dates)
    end     = max(dates) + timedelta(days=cfg.min_paper_lead_time_days)

    schedule: Dict[str, date] = {}
    active:   Set[str]        = set()

    while current <= end and len(schedule) < len(sub_map):
        # retire finished drafts
        active = {
            sid
            for sid in active
            if current < schedule[sid] + _draft_delta(sub_map[sid], cfg)
        }

        # gather ready submissions
        ready: List[str] = []
        for sid in topo:
            if sid in schedule:
                continue
            s = sub_map[sid]
            if not _deps_satisfied(s, schedule, sub_map, cfg, current):
                continue
            if current < s.earliest_start_date:
                continue
            ready.append(sid)

        # schedule up to concurrency limit
        for sid in ready:
            if len(active) >= cfg.max_concurrent_submissions:
                break
            if not _meets_deadline(sub_map[sid], conf_map, current, cfg):
                continue
            schedule[sid] = current
            active.add(sid)

        current += timedelta(days=1)

    if len(schedule) != len(sub_map):
        missing = [sid for sid in sub_map if sid not in schedule]
        raise RuntimeError(f"Could not schedule submissions: {missing}")

    return schedule

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

def _auto_link_abstract_paper(subs: List[Submission]) -> None:
    """Link abstract→paper pairs (same conf + title, case-insensitive)."""
    groups: Dict[Tuple[Optional[str], str], List[Submission]] = {}
    for s in subs:
        groups.setdefault((s.conference_id, s.title.lower()), []).append(s)

    for g in groups.values():
        abs_  = [s for s in g if s.kind == SubmissionType.ABSTRACT]
        paper = [s for s in g if s.kind == SubmissionType.PAPER]
        if len(abs_) == 1 and len(paper) == 1 and abs_[0].id not in paper[0].depends_on:
            paper[0].depends_on.append(abs_[0].id)

# --------------------------------------------------------------------------- #

def _deps_satisfied(
    sub: Submission,
    sched: Dict[str, date],
    sub_map: Dict[str, Submission],
    cfg: Config,
    now: date,
) -> bool:
    """All dependencies scheduled & gap satisfied?"""

    gap_mod    = relativedelta(days=cfg.mod_to_paper_gap_days)
    gap_paper  = relativedelta(
        days=getattr(cfg, "paper_parent_gap_days", 90)  # default 3 months
    )

    for dep_id in sub.depends_on:
        if dep_id not in sched:
            return False
        dep        = sub_map[dep_id]
        finish     = sched[dep_id] + _draft_delta(dep, cfg)
        gap_needed = gap_mod if dep.conference_id is None else gap_paper
        if now < finish + gap_needed:
            return False
    return True

# --------------------------------------------------------------------------- #

def _draft_delta(sub: Submission, cfg: Config) -> timedelta:
    """Draft duration for a submission."""
    days = (
        cfg.min_abstract_lead_time_days
        if sub.kind == SubmissionType.ABSTRACT
        else cfg.min_paper_lead_time_days
    )
    return timedelta(days=days)

def _meets_deadline(sub: Submission,
                    conf_map: Dict[str, Conference],
                    start: date,
                    cfg: Config) -> bool:
    if not sub.conference_id:
        return True
    conf = conf_map[sub.conference_id]
    dl   = conf.deadlines.get(sub.kind)
    if not dl:
        return True
    finish = start + _draft_delta(sub, cfg) - timedelta(days=1)
    return finish <= dl

# --------------------------------------------------------------------------- #

def _topological_order(sub_map: Dict[str, Submission]) -> List[str]:
    indeg = {sid: 0 for sid in sub_map}
    for s in sub_map.values():
        for d in s.depends_on:
            indeg[s.id] += 1
    q: List[str] = [sid for sid, n in indeg.items() if n == 0]
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

def _validate_venue_compatibility(sub_map: Dict[str, Submission],
                                  conf_map: Dict[str, Conference]) -> None:
    for s in sub_map.values():
        if not s.conference_id:
            continue
        conf = conf_map[s.conference_id]
        if conf.conf_type == ConferenceType.ENGINEERING and not s.engineering:
            raise ValueError(
                f"Medical submission {s.id} cannot target engineering venue {conf.id}"
            )

# --------------------------------------------------------------------------- #
# Persistence helpers (unchanged)
# --------------------------------------------------------------------------- #

def load_schedule(path: str) -> Dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {r["id"]: r["start_month_index"] for r in rows}

def save_schedule(schedule: Dict[str, date],
                  submissions: List[Submission],
                  path: str) -> None:
    rows = [{
        "id": sid,
        "title": next(sub for sub in submissions if sub.id == sid).title,
        "start_date": dt.isoformat(),
    } for sid, dt in schedule.items()]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
