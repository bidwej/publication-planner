import json
from scheduler import greedy_schedule as scheduler_greedy
import os
from typing import Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

class Planner:
    def __init__(self, config_path: str) -> None:
        """Initialize Planner with Config from loader."""
        self.cfg = load_config(config_path)
    def validate_config(self) -> None:
        # No-op
        pass

    def generate_monthly_table(self):
        from datetime import datetime as _dt
        events_by_month: Dict[str, list[str]] = {}
        for c in self.config.get("conferences", []):
            for key in ("abstract_deadline", "full_paper_deadline"):
                d_str = c.get(key)
                if not d_str:
                    continue
                try:
                    dt = _dt.fromisoformat(d_str).date()
                except Exception:
                    dt = _dt.fromisoformat(d_str.split("T")[0]).date()
                month = f"{dt.year}-{dt.month:02d}"
                events_by_month.setdefault(month, []).append(c["name"])
        rows = []
        for month in sorted(events_by_month):
            names = sorted(set(events_by_month[month]))
            deadlines = ", ".join(names)
            rows.append({
                "Month": month,
                "Deadlines": deadlines,
                "Active Papers": ""
            })
        return rows

    def schedule(self, strategy: str):
        """Run scheduling strategy to produce mod and paper dates."""
        if strategy != "greedy":
            raise ValueError(f"Unknown strategy: {strategy}")
        full_sched = scheduler_greedy(self.cfg)
        # Split into mod and paper schedules
        mod_sched = {}
        paper_sched = {}
        for sid, dt in full_sched.items():
            if sid.endswith("-wrk"):
                # mod submissions like mod##-wrk
                num = int(sid[3:sid.find("-")])
                mod_sched[num] = dt
            elif sid.endswith("-pap"):
                pid = sid.split("-")[0]
                paper_sched[pid] = dt
        return mod_sched, paper_sched
        if strategy != "greedy":
            raise ValueError(f"Unknown strategy: {strategy}")
        return self.greedy_schedule()

    
    def greedy_schedule(self):
        """Greedy schedule with priority weighting."""
        # Priority weights
        pw = self.priority_weights
        # Mods all at month 0, sorted by weight
        mod_sched: dict = {}
        mods_sorted = sorted(self.mods, key=lambda m: pw.get("mod", 1.0), reverse=True)
        for m in mods_sorted:
            mid = m.get("id") or m.get("mod_id")
            mod_sched[mid] = 0

        # Papers respecting parent dependencies, scheduled by weight
        paper_sched: dict = {}
        base = 0
        unscheduled = set(self.papers.keys())
        while unscheduled:
            # Identify ready papers
            ready = [pid for pid in unscheduled if all(par in paper_sched for par in self.papers[pid].get("parent_papers", []))]
            # Sort ready by weight (default to engineering_paper)
            ready_sorted = sorted(
                ready,
                key=lambda pid: pw.get("engineering_paper", 1.0),
                reverse=True
            )
            progressed = False
            for pid in ready_sorted:
                p = self.papers[pid]
                parents = p.get("parent_papers", [])
                if parents:
                    month_idx = base
                    for par in parents:
                        par_idx = paper_sched[par]
                        draft = self.papers[par].get("draft_window_months", 0)
                        lead = p.get(
                            "lead_time_from_parents",
                            self.config.get("default_paper_lead_time_months", 0)
                        )
                        candidate = par_idx + draft + lead
                        if candidate > month_idx:
                            month_idx = candidate
                    paper_sched[pid] = month_idx
                else:
                    paper_sched[pid] = base
                unscheduled.remove(pid)
                progressed = True
            if not progressed:
                for pid in unscheduled:
                    paper_sched[pid] = base
                break

        return mod_sched, paper_sched

        # Integer-based schedule with concurrency limits

        # Determine concurrency limits
        max_mods = self.config.get("max_concurrent_mods", self.config.get("max_concurrent_submissions", 1))
        max_papers = self.config.get("max_concurrent_papers", self.config.get("max_concurrent_submissions", 1))

        # Schedule mods with concurrency
        mod_sched: Dict[Any, int] = {}
        month = 0
        count_mod = 0
        for m in self.mods:
            mid = m.get("id") or m.get("mod_id")
            if count_mod >= max_mods:
                month += 1
                count_mod = 0
            mod_sched[mid] = month
            count_mod += 1

        # Unconstrained paper scheduling respecting dependencies
        raw_paper_sched: Dict[Any, int] = {}
        base = 0
        unscheduled = set(self.papers.keys())
        while unscheduled:
            progressed = False
            for pid in list(unscheduled):
                p = self.papers[pid]
                # Dependencies: parent_papers
                parents = p.get("parent_papers", [])
                # mod_dependencies also enforced
                mod_deps = p.get("mod_dependencies", [])
                # Check both dependencies scheduled
                if all(par in raw_paper_sched for par in parents) and all(md in mod_sched for md in mod_deps):
                    # Determine earliest month based on dependencies
                    earliest = base
                    # Parent dependencies
                    if parents:
                        for par in parents:
                            par_idx = raw_paper_sched[par]
                            draft = self.papers[par].get("draft_window_months", 0)
                            lead = p.get("lead_time_from_parents", self.config.get("default_paper_lead_time_months", 0))
                            candidate = par_idx + draft + lead
                            earliest = max(earliest, candidate)
                    # mod dependencies
                    if mod_deps:
                        for md in mod_deps:
                            dep_month = mod_sched.get(md, 0)
                            gap = self.config.get("mod_to_paper_gap_days", 0) // 30
                            earliest = max(earliest, dep_month + gap)
                    raw_paper_sched[pid] = earliest
                    unscheduled.remove(pid)
                    progressed = True
            if not progressed:
                # assign remaining with base
                for pid in unscheduled:
                    raw_paper_sched[pid] = base
                break

        # Enforce concurrency for papers
        paper_sched: Dict[Any, int] = {}
        month_counts: Dict[int, int] = {}
        # Sort by earliest month then by id for tie-break
        for pid, raw_month in sorted(raw_paper_sched.items(), key=lambda x: (x[1], x[0])):
            mth = raw_month
            while month_counts.get(mth, 0) >= max_papers:
                mth += 1
            paper_sched[pid] = mth
            month_counts[mth] = month_counts.get(mth, 0) + 1

        return mod_sched, paper_sched

    # Aliases
    greedy_schedule = schedule
    solve_lp_relaxed = schedule
    solve_lp_relaxed = greedy_schedule
    solve_lp_relaxed = greedy_schedule
