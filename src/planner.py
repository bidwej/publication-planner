import os, json
from typing import Any, Dict, List, Tuple
from datetime import date

from loader import load_config
from scheduler import greedy_schedule as scheduler_greedy
from type import Config, SubmissionType


class Planner:
    def __init__(self, config_path: str):
        self.cfg: Config = load_config(config_path)

    def validate_config(self) -> None:
        pass  # no-op

    def schedule(self, strategy: str) -> Tuple[Dict[int, Any], Dict[str, Any]]:
        if strategy != "greedy":
            raise ValueError(f"Unknown strategy: {strategy}")
        full = scheduler_greedy(self.cfg)
        mod_sched: Dict[int, Any] = {}
        paper_sched: Dict[str, Any] = {}
        for sid, dt in full.items():
            if sid.endswith("-wrk"):
                mod_sched[int(sid[3 : sid.find("-")])] = dt
            elif sid.endswith("-pap"):
                paper_sched[sid.split("-")[0]] = dt
        return mod_sched, paper_sched

    def greedy_schedule(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        pw = self.cfg.priority_weights or {}

        # abstracts = "mods"
        mods = [s for s in self.cfg.submissions if s.kind == SubmissionType.ABSTRACT]
        mod_sched = {
            s.id: 0
            for s in sorted(mods, key=lambda s: pw.get(s.id, 1.0), reverse=True)
        }

        # papers
        papers = {s.id: s for s in self.cfg.submissions if s.kind == SubmissionType.PAPER}
        paper_sched: Dict[str, int] = {}
        base = 0
        unscheduled = set(papers)

        while unscheduled:
            ready = sorted(
                (pid for pid in unscheduled
                 if all(dep in paper_sched for dep in papers[pid].depends_on)),
                key=lambda pid: pw.get(pid, 1.0),
                reverse=True
            )
            if not ready:
                for pid in unscheduled:
                    paper_sched[pid] = base
                break
            for pid in ready:
                sub = papers[pid]
                month = base
                for dep in sub.depends_on:
                    month = max(month,
                                paper_sched[dep] + self.cfg.paper_parent_gap_days // 30)
                paper_sched[pid] = month
                unscheduled.remove(pid)

        return mod_sched, paper_sched

    def concurrent_schedule(self) -> Tuple[Dict[str, int], Dict[str, int]]:
        mods = [s for s in self.cfg.submissions if s.kind == SubmissionType.ABSTRACT]
        max_mods = self.cfg.max_concurrent_submissions
        mod_sched: Dict[str, int] = {}
        month = count = 0
        for s in mods:
            if count >= max_mods:
                month += 1
                count = 0
            mod_sched[s.id] = month
            count += 1

        papers = [s for s in self.cfg.submissions if s.kind == SubmissionType.PAPER]
        max_papers = self.cfg.max_concurrent_submissions
        raw_sched: Dict[str, int] = {}
        base = 0
        unscheduled = {s.id for s in papers}

        while unscheduled:
            progressed = False
            for pid in list(unscheduled):
                sub = next(s for s in papers if s.id == pid)
                if all(dep in raw_sched for dep in sub.depends_on):
                    earliest = base
                    for dep in sub.depends_on:
                        earliest = max(earliest,
                                       raw_sched[dep] + self.cfg.paper_parent_gap_days // 30)
                    raw_sched[pid] = earliest
                    unscheduled.remove(pid)
                    progressed = True
            if not progressed:
                for pid in unscheduled:
                    raw_sched[pid] = base
                break

        paper_sched: Dict[str, int] = {}
        counts: Dict[int, int] = {}
        for pid, r in sorted(raw_sched.items(), key=lambda x: (x[1], x[0])):
            m = r
            while counts.get(m, 0) >= max_papers:
                m += 1
            paper_sched[pid] = m
            counts[m] = counts.get(m, 0) + 1

        return mod_sched, paper_sched


# backward‐compatible alias
Planner.solve_lp_relaxed = Planner.greedy_schedule