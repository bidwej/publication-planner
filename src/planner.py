import json, os
from typing import Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from loader import load_config
from scheduler import greedy_schedule as scheduler_greedy

class Planner:
    def __init__(self, config_path: str):
        self.cfg = load_config(config_path)

    def validate_config(self):
        pass  # no-op

    def schedule(self, strategy: str) -> tuple[Dict[Any, Any], Dict[Any, Any]]:
        # top‐level scheduling via external greedy scheduler
        if strategy != "greedy":
            raise ValueError(f"Unknown strategy: {strategy}")
        full = scheduler_greedy(self.cfg)
        mod_sched, paper_sched = {}, {}
        for sid, dt in full.items():
            if sid.endswith("-wrk"):
                # mod##-wrk → integer key
                mod_sched[int(sid[3:sid.find("-")])] = dt
            elif sid.endswith("-pap"):
                # pid-pap → pid key
                paper_sched[sid.split("-")[0]] = dt
        return mod_sched, paper_sched

    def greedy_schedule(self) -> tuple[Dict[Any, int], Dict[Any, int]]:
        # priority‐weighted custom scheduling
        pw = self.priority_weights
        # all mods at month 0, sorted by weight
        mod_sched = {
            (m.get("id") or m.get("mod_id")): 0
            for m in sorted(self.mods, key=lambda m: pw.get("mod", 1.0), reverse=True)
        }
        paper_sched = {}
        base = 0
        unscheduled = set(self.papers)
        while unscheduled:
            ready = sorted(
                (pid for pid in unscheduled
                 if all(par in paper_sched for par in self.papers[pid].get("parent_papers", []))),
                key=lambda pid: pw.get("engineering_paper", 1.0),
                reverse=True
            )
            if not ready:
                # break cycles by placing remaining at base
                for pid in unscheduled:
                    paper_sched[pid] = base
                break
            for pid in ready:
                p = self.papers[pid]
                month = base
                for par in p.get("parent_papers", []):
                    par_idx = paper_sched[par]
                    draft = self.papers[par].get("draft_window_months", 0)
                    lead = p.get("lead_time_from_parents",
                                 self.cfg.get("default_paper_lead_time_months", 0))
                    month = max(month, par_idx + draft + lead)
                paper_sched[pid] = month
                unscheduled.remove(pid)
        return mod_sched, paper_sched

    def concurrent_schedule(self) -> tuple[Dict[Any, int], Dict[Any, int]]:
        # integer‐based schedule with concurrency limits
        max_mods = self.cfg.get("max_concurrent_mods",
                                 self.cfg.get("max_concurrent_submissions", 1))
        max_papers = self.cfg.get("max_concurrent_papers",
                                   self.cfg.get("max_concurrent_submissions", 1))

        # schedule mods round‐robin by month
        mod_sched, month, count = {}, 0, 0
        for m in self.mods:
            mid = m.get("id") or m.get("mod_id")
            if count >= max_mods:
                month += 1
                count = 0
            mod_sched[mid] = month
            count += 1

        # unconstrained paper scheduling with dependencies
        raw, base = {}, 0
        unscheduled = set(self.papers)
        while unscheduled:
            progressed = False
            for pid in list(unscheduled):
                p = self.papers[pid]
                parents = p.get("parent_papers", [])
                mod_deps = p.get("mod_dependencies", [])
                if all(par in raw for par in parents) and all(md in mod_sched for md in mod_deps):
                    earliest = base
                    for par in parents:
                        par_idx = raw[par]
                        draft = self.papers[par].get("draft_window_months", 0)
                        lead = p.get("lead_time_from_parents",
                                     self.cfg.get("default_paper_lead_time_months", 0))
                        earliest = max(earliest, par_idx + draft + lead)
                    for md in mod_deps:
                        dep_month = mod_sched[md]
                        gap = self.cfg.get("mod_to_paper_gap_days", 0) // 30
                        earliest = max(earliest, dep_month + gap)
                    raw[pid] = earliest
                    unscheduled.remove(pid)
                    progressed = True
            if not progressed:
                for pid in unscheduled:
                    raw[pid] = base
                break

        # enforce concurrency for papers
        paper_sched, counts = {}, {}
        for pid, r in sorted(raw.items(), key=lambda x: (x[1], x[0])):
            mth = r
            while counts.get(mth, 0) >= max_papers:
                mth += 1
            paper_sched[pid] = mth
            counts[mth] = counts.get(mth, 0) + 1

        return mod_sched, paper_sched

# alias for backward compatibility
Planner.solve_lp_relaxed = Planner.greedy_schedule
