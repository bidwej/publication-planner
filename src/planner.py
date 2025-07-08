from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from collections import defaultdict

import numpy as np
import scipy.optimize

from type import (
    Config,
    Submission,
    SubmissionType,
    ConferenceType,
)

class Planner:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.sub_map: Dict[str, Submission] = {s.id: s for s in cfg.submissions}
        self.conf_map = {c.id: c for c in cfg.conferences}

        self._build_calendar()
        self._validate()

    # ------------------------------------------------------------------ #
    # PUBLIC API
    # ------------------------------------------------------------------ #

    def greedy_schedule(self) -> Dict[str, int]:
        """
        Returns a dict {submission_id -> month_index (int)}
        that satisfies all dependencies and capacity.
        """
        # Topological order --------------------------------------------
        topo = self._topological_order()
        schedule: Dict[str, int] = {}
        active: set[str] = set()

        for t in range(len(self.months)):
            # retire finished rows
            for sid in list(active):
                s = self.sub_map[sid]
                if t >= schedule[sid] + s.draft_window_months:
                    active.remove(sid)

            # enqueue rows whose deps are all satisfied
            ready = [
                sid for sid in topo
                if sid not in schedule
                and all(dep in schedule for dep in self.sub_map[sid].depends_on)
            ]
            # capacity
            for sid in ready:
                if len(active) >= self.cfg.max_concurrent_submissions:
                    break
                # earliest allowed by internal_ready_date
                earliest = max(
                    self._month_of(self.sub_map[sid].internal_ready_date),
                    max(
                        (schedule[d] + self.sub_map[d].draft_window_months)
                        for d in self.sub_map[sid].depends_on
                    ) if self.sub_map[sid].depends_on else 0,
                )
                if t < earliest:
                    continue  # can't yet
                # external_deadline check
                ext = self.sub_map[sid].external_due_date
                if ext is not None:
                    finish = t + self.sub_map[sid].draft_window_months
                    if finish > self._month_of(ext):
                        continue  # would miss CFP
                # start it
                schedule[sid] = t
                active.add(sid)

            if len(schedule) == len(self.sub_map):
                break

        if len(schedule) != len(self.sub_map):
            raise RuntimeError("Greedy scheduler could not place every row.")

        return schedule

    # ------------------------------------------------------------------ #
    # PRIVATE HELPERS
    # ------------------------------------------------------------------ #

    def _build_calendar(self) -> None:
        """Build month list from earliest internal_ready to latest ext deadline."""
        all_dates: List[date] = []
        for s in self.sub_map.values():
            all_dates.append(s.internal_ready_date)
            if s.external_due_date:
                all_dates.append(s.external_due_date)

        start = min(all_dates)
        end   = max(all_dates)
        # pad by default_lead_time
        end = end + relativedelta(months=self.cfg.default_lead_time_months)

        self.months: List[datetime] = []
        cur = datetime(start.year, start.month, 1)
        while cur.date() <= end:
            self.months.append(cur)
            cur += relativedelta(months=1)

        self.month_index: Dict[int, int] = {
            (m.year, m.month): idx for idx, m in enumerate(self.months)
        }

    def _month_of(self, dt: date) -> int:
        return self.month_index[(dt.year, dt.month)]

    # ---------- validation ------------------------------------------- #
    def _validate(self) -> None:
        # dependency IDs exist
        for s in self.sub_map.values():
            for d in s.depends_on:
                if d not in self.sub_map:
                    raise ValueError(f"{s.id} depends on missing {d}")

        # venue compatibility
        for s in self.sub_map.values():
            if s.conference_id:
                conf = self.conf_map[s.conference_id]
                if conf.conf_type == ConferenceType.ENGINEERING:
                    continue
                # Medical venue: disallow engineering-only work if flagged
                if s.engineering and conf.conf_type == ConferenceType.MEDICAL:
                    raise ValueError(f"Engineering row {s.id} cannot go to medical venue")

    # ---------- topo sort -------------------------------------------- #
    def _topological_order(self) -> List[str]:
        indeg = {sid: 0 for sid in self.sub_map}
        for s in self.sub_map.values():
            for d in s.depends_on:
                indeg[s.id] += 1

        queue = [sid for sid, k in indeg.items() if k == 0]
        order = []
        while queue:
            sid = queue.pop(0)
            order.append(sid)
            for s2 in self.sub_map.values():
                if sid in s2.depends_on:
                    indeg[s2.id] -= 1
                    if indeg[s2.id] == 0:
                        queue.append(s2.id)

        if len(order) != len(self.sub_map):
            raise RuntimeError("Dependency cycle detected")
        return order
