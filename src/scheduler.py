from __future__ import annotations
import json
from datetime import date, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dateutil.relativedelta import relativedelta
from type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
    Conference,
)

# --------------------------------------------------------------------------- #
# Public entry-point
# --------------------------------------------------------------------------- #
def greedy_schedule(cfg: Config) -> Dict[str, date]:
    """
    Greedy daily scheduler for abstracts & papers with priority weighting
    and blackout date handling.
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
    end = max(dates) + timedelta(days=cfg.min_paper_lead_time_days * 2)
    schedule: Dict[str, date] = {}
    active: Set[str] = set()
    # Early abstract scheduling if enabled
    if cfg.scheduling_options and cfg.scheduling_options.get("enable_early_abstract_scheduling", False):
        abstract_advance = cfg.scheduling_options.get("abstract_advance_days", 30)
        _schedule_early_abstracts(sub_map, conf_map, schedule, abstract_advance, cfg)
    while current <= end and len(schedule) < len(sub_map):
        # Skip blackout dates
        if not _is_working_day(current, cfg):
            current += timedelta(days=1)
            continue
        # retire finished drafts
        active = {
            sid
            for sid in active
            if _get_end_date(schedule[sid], sub_map[sid], cfg) > current
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
        # Sort by priority weight
        ready = _sort_by_priority(ready, sub_map, cfg)
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
# Blackout date handling
# --------------------------------------------------------------------------- #
def _is_working_day(date_val: date, cfg: Config) -> bool:
    """Check if a date is a working day (not weekend or blackout)."""
    # Weekend check
    if cfg.scheduling_options and cfg.scheduling_options.get("enable_blackout_periods", False):
        if date_val.weekday() in [5, 6]:  # Saturday, Sunday
            return False
        # Blackout dates check
        if cfg.blackout_dates and date_val in cfg.blackout_dates:
            return False
    return True

def _add_working_days(start_date: date, duration_days: int, cfg: Config) -> date:
    """Add working days to a date, skipping blackouts."""
    if not cfg.scheduling_options or not cfg.scheduling_options.get("enable_blackout_periods", False):
        return start_date + timedelta(days=duration_days)
    current = start_date
    days_added = 0
    while days_added < duration_days:
        current += timedelta(days=1)
        if _is_working_day(current, cfg):
            days_added += 1
    return current

def _get_end_date(start_date: date, sub: Submission, cfg: Config) -> date:
    """Get end date for a submission accounting for blackouts."""
    duration = _get_duration_days(sub, cfg)
    if duration == 0:  # Abstract milestone
        return start_date
    return _add_working_days(start_date, duration - 1, cfg)

# --------------------------------------------------------------------------- #
# Priority handling
# --------------------------------------------------------------------------- #
def _sort_by_priority(
    ready: List[str], sub_map: Dict[str, Submission], cfg: Config) -> List[str]:
    """Sort ready submissions by priority weight."""
    def get_priority(sid: str) -> float:
        sub = sub_map[sid]
        weights = cfg.priority_weights or {}
        if sub.kind == SubmissionType.ABSTRACT:
            return weights.get("abstract", 0.5)
        elif sub.conference_id is None:  # Mod
            return weights.get("mod", 1.5)
        elif sub.engineering:
            return weights.get("engineering_paper", 2.0)
        else:
            return weights.get("medical_paper", 1.0)
    return sorted(ready, key=get_priority, reverse=True)

# --------------------------------------------------------------------------- #
# Early abstract scheduling
# --------------------------------------------------------------------------- #
def _schedule_early_abstracts(
    sub_map: Dict[str, Submission],
    conf_map: Dict[str, Conference],
    schedule: Dict[str, date],
    advance_days: int,
    cfg: Config,
) -> None:
    """Schedule abstracts early during slack periods."""
    # Schedule abstracts as early as possible within advance window
    for abstract in [s for s in sub_map.values() if s.kind == SubmissionType.ABSTRACT and s.id not in schedule]:
        # Skip if no conference
        if not abstract.conference_id:
            continue
        conf = conf_map.get(abstract.conference_id)
        if not conf:
            continue
        abs_deadline = conf.deadlines.get(SubmissionType.ABSTRACT)
        if not abs_deadline:
            continue
        # Determine when dependencies are done
        deps_ready = abstract.earliest_start_date
        for dep_id in abstract.depends_on:
            if dep_id in schedule:
                dep_end = _get_end_date(schedule[dep_id], sub_map[dep_id], cfg)
                if dep_end > deps_ready:
                    deps_ready = dep_end
        # Compute ideal advance start date
        ideal_start = abs_deadline - timedelta(days=advance_days)
        # Choose the later of deps_ready and ideal_start
        start_date = deps_ready if deps_ready > ideal_start else ideal_start
        # Adjust to next working day
        while not _is_working_day(start_date, cfg):
            start_date += timedelta(days=1)
        # Ensure finish before the abstract deadline
        finish = _get_end_date(start_date, abstract, cfg)
        if finish <= abs_deadline:
            schedule[abstract.id] = start_date

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _auto_link_abstract_paper(subs: List[Submission]) -> None:
    """Link abstract→paper pairs (same conf + title, case-insensitive)."""
    groups: Dict[Tuple[Optional[str], str], List[Submission]] = {}
    for s in subs:
        groups.setdefault((s.conference_id, s.title.lower()), []).append(s)
    for g in groups.values():
        abs_ = [s for s in g if s.kind == SubmissionType.ABSTRACT]
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
    gap_mod = timedelta(days=cfg.mod_to_paper_gap_days)
    gap_paper = timedelta(days=cfg.paper_parent_gap_days)
    for dep_id in sub.depends_on:
        if dep_id not in sched:
            return False
        dep = sub_map[dep_id]
        finish = _get_end_date(sched[dep_id], dep, cfg)
        gap_needed = gap_mod if dep.conference_id is None else gap_paper
        if now < finish + gap_needed:
            return False
    return True

# --------------------------------------------------------------------------- #
def _get_duration_days(sub: Submission, cfg: Config) -> int:
    """Get duration in days for a submission."""
    if sub.kind == SubmissionType.ABSTRACT:
        return cfg.min_abstract_lead_time_days  # 0 for milestones
    else:
        return cfg.min_paper_lead_time_days

def _draft_delta(sub: Submission, cfg: Config) -> timedelta:
    """Draft duration for a submission."""
    return timedelta(days=_get_duration_days(sub, cfg))

def _meets_deadline(
    sub: Submission, conf_map: Dict[str, Conference], start: date, cfg: Config) -> bool:
    if not sub.conference_id:
        return True
    conf = conf_map[sub.conference_id]
    dl = conf.deadlines.get(sub.kind)
    if not dl:
        return True
    finish = _get_end_date(start, sub, cfg)
    return finish <= dl

# --------------------------------------------------------------------------- #
def _topological_order(sub_map: Dict[str, Submission]) -> List[str]:
    indeg = {sid: 0 for sid in sub_map}
    for s in sub_map.values():
        for d in s.depends_on:
            if d in sub_map:  # Only count dependencies that exist
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

def _validate_venue_compatibility(
    sub_map: Dict[str, Submission], conf_map: Dict[str, Conference]) -> None:
    for s in sub_map.values():
        if not s.conference_id:
            continue
        conf = conf_map[s.conference_id]
        if conf.conf_type == ConferenceType.ENGINEERING and not s.engineering:
            raise ValueError(
                f"Medical submission {s.id} cannot target engineering venue {conf.id}"
            )

# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #
def load_schedule(path: str) -> Dict[str, date]:
    """Load schedule from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {r["id"]: date.fromisoformat(r["start_date"]) for r in rows}

def save_schedule(
    schedule: Dict[str, date], submissions: List[Submission], path: str) -> None:
    """Save schedule to JSON file."""
    rows = [
        {
            "id": sid,
            "title": next(sub for sub in submissions if sub.id == sid).title,
            "start_date": dt.isoformat(),
        }
        for sid, dt in schedule.items()
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)