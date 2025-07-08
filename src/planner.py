import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Planner:

    def markdown_mod_schedule(self):
        """
        Returns a markdown table of PCCP mods with their due dates and slack.
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        lines = [
            "## PCCP Mods Schedule",
            "| Mod ID | Title                    | Phase | Est Data Ready | With Slack     |",
            "|--------|--------------------------|-------|----------------|----------------|"
        ]
        slack = self.config.get("default_mod_lead_time_months", 0)
        for m in self.mods:
            dt = datetime.fromisoformat(m["est_data_ready"])
            dt_slack = dt + relativedelta(months=slack)
            lines.append(
                f"| {m['id']:<6} | {m['title']:<24} | {m['phase']:<5} | "
                f"{dt.strftime('%Y-%m-%d')}     | {dt_slack.strftime('%Y-%m-%d')} |"
            )
        return "\n".join(lines)


    

    def validate_config(self):
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        """
        Validates config structure and schedule metrics including:
        - Top-level keys and types
        - Counts: 17 mods, 20 papers, 14 conferences
        - Default lead times and max concurrency
        - References integrity (mods, parent papers, conferences)
        - Schedule metrics: months, conferences, attendance
        - Mod-to-paper alignment
        - Abstract before full submission alignment
        """
        # Required top-level keys and types
        required = {
            "default_paper_lead_time_months": int,
            "default_mod_lead_time_months": int,
            "pccp_mods": list,
            "ed_papers": list,
            "conferences": list,
            "max_concurrent_papers": int
        , "data_files": dict}
        for k, t in required.items():
            assert k in self.config, f"Missing key: {k}"
            assert isinstance(self.config[k], t), f"Key {k} must be {t}"
        # Check defaults
        assert self.config["default_paper_lead_time_months"] >= 0
        assert self.config["default_mod_lead_time_months"] >= 0
        assert self.config["max_concurrent_papers"] > 0

        # Check counts
        num_mods = len(self.config["pccp_mods"])
        num_papers = len(self.config["ed_papers"])
        num_confs = len(self.config["conferences"])
        assert num_mods == 17, f"Expected 17 mods, found {num_mods}"
        assert num_papers == 20, f"Expected 20 papers, found {num_papers}"
        assert num_confs == 14, f"Expected 14 conferences, found {num_confs}"

        # Integrity of dependencies and references
        mod_ids = {m["id"] for m in self.config["pccp_mods"]}
        paper_ids = {p["id"] for p in self.config["ed_papers"]}
        conf_names = {c["name"] for c in self.config["conferences"]}
        required_mod_fields = {"id","title","phase","est_data_ready","free_slack_months","penalty_cost_per_month"}
        for m in self.config["pccp_mods"]:
            assert required_mod_fields.issubset(m.keys()), f"Missing fields in mod {m}"
        required_paper_fields = {"id","title","mod_dependencies","parent_papers","draft_window_months","conference_families"}
        for p in self.config["ed_papers"]:
            assert required_paper_fields.issubset(p.keys()), f"Missing fields in paper {p['id']}"
            for mid in p["mod_dependencies"]:
                assert mid in mod_ids, f"Invalid mod_dependencies in paper {p['id']}"
            for par in p["parent_papers"]:
                assert par in paper_ids, f"Invalid parent_paper in paper {p['id']}"
            for fam in p["conference_families"]:
                assert fam in conf_names, f"Invalid conference_families in paper {p['id']}"
            assert isinstance(p["draft_window_months"], int) and p["draft_window_months"]>0

        required_conf_fields = {"name","full_paper_deadline","abstract_deadline","recurrence"}
        for c in self.config["conferences"]:
            assert required_conf_fields.issubset(c.keys()), f"Missing fields in conference {c.get('name')}"
            assert c["recurrence"] in ("annual","biennial"), f"Invalid recurrence in {c['name']}"

        # Generate schedule
        mod_sched, paper_sched = self.schedule("greedy")
        rows = self.generate_monthly_table()
        months_count = len(rows)
        print(f"Total schedule months: {months_count}")
        # Check conferences represented
        all_deads = []
        for row in rows:
            for d in row.get("Deadlines","").split("; "):
                if d:
                    all_deads.append(d.split()[0])
        unique_confs = set(all_deads)
        assert len(unique_confs) <= num_confs, f"Unique confs {len(unique_confs)} exceeds total {num_confs}"
        print(f"Conferences with deadlines: {len(unique_confs)}")

        # Attended vs missed
        attended=missed=0
        for row in rows:
            active = [p.strip() for p in row.get("Active Papers","").split(",") if p.strip()]
            for d in row.get("Deadlines","").split("; "):
                if not d: continue
                conf = d.split()[0]
                # eligible papers for this conf
                elig = [pid for pid,p in self.papers.items() if conf in p["conference_families"]]
                if any(pid in active for pid in elig):
                    attended+=1
                else:
                    missed+=1
        print(f"Deadlines attended: {attended}, missed: {missed}")

        # Mod-to-paper alignment
        for pid,p in self.papers.items():
            start_idx = paper_sched.get(pid)
            for mid in p["mod_dependencies"]:
                mod_idx = mod_sched.get(mid)
                assert start_idx>=mod_idx, f"Paper {pid} starts before mod {mid}"

        # Abstract before full alignment
        # Build deadline occurrences
        for c in self.config["conferences"]:
            base_full = c.get("full_paper_deadline")
            base_abs = c.get("abstract_deadline")
            freq = c.get("recurrence")
            if not base_full or not base_abs: 
                continue
            dt_full0 = datetime.fromisoformat(base_full)
            dt_abs0 = datetime.fromisoformat(base_abs)
            for year in range(self.months[0].year, self.months[-1].year+1):
                if freq=="biennial" and (year % 2 != dt_full0.year % 2): continue
                dfull = dt_full0.replace(year=year)
                dabs = dt_abs0.replace(year=year)
                key_full = dfull.strftime("%Y-%m")
                key_abs = dabs.strftime("%Y-%m")
                idx_full = self.month_indices.get(datetime(dfull.year, dfull.month,1))
                if idx_full is None:
                    continue
            
                idx_abs = self.month_indices.get(datetime(dabs.year, dabs.month,1))
                if idx_abs is None:
                    continue
                
            if idx_full is None or idx_abs is None:
                continue
            # For each paper eligible# For each paper eligible
                for pid,p in self.papers.items():
                    if c["name"] not in p["conference_families"]: continue
                    # must be active at abstract and full months
                    row_abs = rows[idx_abs]
                    row_full = rows[idx_full]
                    active_abs = pid in [x.strip() for x in row_abs["Active Papers"].split(",")]
                    active_full = pid in [x.strip() for x in row_full["Active Papers"].split(",")]
                    assert active_abs, f"Paper {pid} not active at abstract deadline {key_abs}"
                    assert active_full, f"Paper {pid} not active at full deadline {key_full}"

        # Concurrency check
        max_active = max(len([p for p in row.get("Active Papers","").split(",") if p.strip()]) for row in rows)
        assert max_active <= self.config["max_concurrent_papers"], "Concurrency exceeded"
        print(f"Max concurrency {max_active} OK")

    def __init__(self, config_path=None):
        if config_path is None:
            base = os.path.dirname(__file__)
            config_path = os.path.join(base, '..', 'config.json')
        with open(config_path) as f:
            self.config = json.load(f)
        self._prepare()

    def _prepare(self):
                # Load mods from data file
        mods_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config["data_files"]["mods"])
        with open(mods_path) as mf:
            self.mods = json.load(mf)
        # Mirror into config for backwards compatibility/tests
        self.config["pccp_mods"] = self.mods
        # Derive mod_dependencies for backward compatibility/tests
        self.config["mod_dependencies"] = [
            {"from_mod": m["id"], "to_mod": m["next_mod"]}
            for m in self.mods if m.get("next_mod") is not None
        ]
        self.mod_ready = {m["id"]: datetime.fromisoformat(m["est_data_ready"]) for m in self.mods}
                # Load papers from data file
        papers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config["data_files"]["papers"])
        with open(papers_path) as pf:
            papers_list = json.load(pf)
        self.papers = {p["id"]: p for p in papers_list}
        # Mirror into config
        self.config["ed_papers"] = papers_list
        # Load conferences from data file
        confs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config["data_files"]["conferences"])
        with open(confs_path) as cf:
            self.conferences = json.load(cf)
        # Mirror into config
        self.config["conferences"] = self.conferences
        dates = list(self.mod_ready.values())
        self.start_date = min(dates) if dates else datetime.now()
        max_draft = max((p["draft_window_months"] for p in self.papers.values()), default=0)
        max_lead = self.config.get("default_paper_lead_time_months", 0)
        last_mod = max(dates) if dates else self.start_date
        self.end_date = last_mod + relativedelta(months=max_draft + max_lead)
        self.months = []
        cur = datetime(self.start_date.year, self.start_date.month, 1)
        while cur <= self.end_date:
            self.months.append(cur)
            cur += relativedelta(months=1)
        self.month_indices = {m: i for i, m in enumerate(self.months)}

    
    def greedy_schedule(self):
        """
        Capacity-aware greedy schedule:
        - Respects mod readiness and parent constraints
        - Allows up to max_concurrent_papers drafting concurrently
        """
        # Compute earliest start indices
        earliest = {}
        def compute_idx(pid):
            if pid in earliest:
                return earliest[pid]
            p = self.papers[pid]
            mod_idxs = []
            # add default_mod_lead_time_months slack
            lead_mod = self.config.get('default_mod_lead_time_months', 0)
            for mid in p.get("mod_dependencies", []):
                dt = self.mod_ready[mid]
                mod_idxs.append(self.month_indices[datetime(dt.year, dt.month, 1)] + lead_mod)
            parent_idxs = []
            for par in p.get("parent_papers", []):
                ps = compute_idx(par)
                lead = p.get("lead_time_from_parents", self.config["default_paper_lead_time_months"])
                parent_idxs.append(ps + self.papers[par]["draft_window_months"] + lead)
            if mod_idxs or parent_idxs:
                start = max(mod_idxs + parent_idxs)
            else:
                start = min(self.month_indices.values())
            earliest[pid] = start
            return start

        # populate earliest for all papers
        for pid in self.papers:
            compute_idx(pid)

        # Mod schedule
        mod_sched = {
            m["id"]: self.month_indices[datetime.fromisoformat(m["est_data_ready"]).replace(day=1)]
            for m in self.mods
        }

        # Capacity-aware scheduling of papers
        capacity = self.config.get("max_concurrent_papers", 1)
        paper_sched = {}
        active = set()
        scheduled = set()
        for t in range(len(self.months)):
            # remove completed
            for pid in list(active):
                if paper_sched[pid] + self.papers[pid]["draft_window_months"] <= t:
                    active.remove(pid)
            # find available
            avail = [pid for pid in self.papers if pid not in scheduled and earliest[pid] <= t]
            # schedule up to capacity
            for pid in sorted(avail, key=lambda x: earliest[x]):
                if len(active) >= capacity:
                    break
                paper_sched[pid] = t
                active.add(pid)
                scheduled.add(pid)
            if len(scheduled) == len(self.papers):
                break

        return mod_sched, paper_sched


    def schedule(self, method="greedy"):
        if method == "greedy":
            return self.greedy_schedule()
        else:
            raise ValueError("Only greedy supported")

    def generate_monthly_table(self):
        # Capacity-aware schedule
        mod_sched, paper_sched = self.greedy_schedule()
        mod_sched, _ = self.greedy_schedule()
        # Build deadline map with recurrence
        deadline_map = {}
        for c in self.config.get("conferences", []):
            base_full = c.get("full_paper_deadline")
            base_abstract = c.get("abstract_deadline")
            freq = c.get("recurrence", "annual")
            for field, label, base_dt in [
                ("full_paper_deadline", "Full", base_full),
                ("abstract_deadline", "Abstract", base_abstract)
            ]:
                if not base_dt:
                    continue
                dt0 = datetime.fromisoformat(base_dt)
                for year in range(self.start_date.year, self.end_date.year+1):
                    if freq == "biennial" and (year % 2 != dt0.year % 2):
                        continue
                    d = dt0.replace(year=year)
                    key = d.strftime("%Y-%m")
                    deadline_map.setdefault(key, []).append(f"{c['name']} {label} Deadline {d.strftime('%Y-%m-%d')}")
        # Build rows
        rows = []
        for idx, mdate in enumerate(self.months):
            mstr = mdate.strftime("%Y-%m")
            active_mods = [f"Mod {mid}" for mid,start in mod_sched.items() if start == idx]
            active_papers = [pid for pid,start in paper_sched.items() if start <= idx < start + self.papers[pid]["draft_window_months"]]
            confs = "; ".join(deadline_map.get(mstr, []))
            rows.append({"Month":mstr, "Active Mods":", ".join(active_mods), "Active Papers":", ".join(active_papers), "Deadlines":confs})
        return rows
    def markdown_annual_summary(self):
        import pandas as pd
        rows = self.generate_monthly_table()
        df = pd.DataFrame(rows)
        df["Year"] = df["Month"].str[:4].astype(int)
        df["ActivePapersCount"] = df["Active Papers"].apply(
            lambda s: len([x for x in s.split(", ") if x.strip()])
        )

        papers_per_year = df.groupby("Year")["ActivePapersCount"].sum().rename("TotalPaperMonths")

        mod_sched, paper_sched = self.schedule("greedy")
        draft_windows = {pid: self.papers[pid]["draft_window_months"] for pid in self.papers}
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        completion_dates = {
            pid: self.months[paper_sched[pid]] + relativedelta(months=draft_windows[pid])
            for pid in paper_sched
        }
        comp_year = {pid: dt.year for pid, dt in completion_dates.items()}
        papers_completed = pd.Series(comp_year).value_counts().sort_index().rename("PapersCompleted")

        concurrency = df.groupby("Year")["ActivePapersCount"].agg(PeakConcurrency="max", AvgConcurrency="mean")
        concurrency["AvgConcurrency"] = concurrency["AvgConcurrency"].round(2)

        df_mod = pd.DataFrame(rows)
        df_mod["ActiveModsCount"] = df_mod["Active Mods"].apply(
            lambda s: len([x for x in s.split(", ") if x.strip()])
        )
        mod_months = df_mod.groupby("Year")["ActiveModsCount"].sum().rename("ModMonths")

        summary = pd.concat(
            [papers_per_year, papers_completed, concurrency, mod_months], axis=1
        ).fillna(0)
        summary = summary.reset_index().astype(
            {"Year": int, "TotalPaperMonths": int, "PapersCompleted": int}
        )

        lines = []
        lines.append(f"## Annual Schedule Summary (Capacity = {self.config.get('max_concurrent_papers')})")
        lines.append("| Year | TotalPaperMonths | PapersCompleted | PeakConcurrency | AvgConcurrency | ModMonths |")
        lines.append("|------|------------------|-----------------|-----------------|----------------|-----------|")
        for _, row in summary.iterrows():
            lines.append(
                f"| {row['Year']} | {row['TotalPaperMonths']} | {row['PapersCompleted']} "
                f"| {row['PeakConcurrency']} | {row['AvgConcurrency']:.2f} | {row['ModMonths']} |"
            )
        lines.append("")
        lines.append("**TotalPaperMonths**: Sum of months with ≥1 active paper")
        lines.append("**PapersCompleted**: Distinct papers finishing that year")
        lines.append("**PeakConcurrency**: Max simultaneous papers (now capped)")
        lines.append("**AvgConcurrency**: Average active papers per month in the year")
        lines.append("**ModMonths**: Number of months with mod completions")
        return "\n".join(lines)
    def markdown_yearly_details(self, year):
        """
        Returns a detailed markdown table for the given year.
        Columns: Month | Active Mods | Active Papers | Deadlines
        """
        import pandas as pd
        rows = self.generate_monthly_table()
        df = pd.DataFrame(rows)
        df['Year'] = df['Month'].str[:4].astype(int)
        df_year = df[df['Year'] == year]
        lines = []
        lines.append(f"## Year {year} Detailed Schedule")
        lines.append("| Month  | Active Mods | Active Papers | Deadlines |")
        lines.append("|--------|-------------|---------------|-----------|")
        for _, row in df_year.iterrows():
            lines.append(
                f"| {row['Month']} | {row['Active Mods'] or 'None'} | "
                f"{row['Active Papers'] or 'None'} | {row['Deadlines'] or 'None'} |"
            )
        return "\n".join(lines)


    def markdown_mod_schedule(self):
        """
        Returns a markdown table of PCCP mods with their due dates and slack.
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        lines = [
            "## PCCP Mods Schedule",
            "| Mod ID | Title                    | Phase | Est Data Ready | With Slack     |",
            "|--------|--------------------------|-------|----------------|----------------|"
        ]
        slack = self.config.get("default_mod_lead_time_months", 0)
        for m in self.mods:
            dt = datetime.fromisoformat(m["est_data_ready"])
            dt_slack = dt + relativedelta(months=slack)
            lines.append(
                f"| {m['id']:<6} | {m['title']:<24} | {m['phase']:<5} | "
                f"{dt.strftime('%Y-%m-%d')}     | {dt_slack.strftime('%Y-%m-%d')} |"
            )
        return "\n".join(lines)



    

    

    

    def markdown_mod_schedule(self):
        """
        Returns a markdown table of PCCP mods with their due dates and slack.
        """
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        lines = []
        lines.append("## PCCP Mods Schedule")
        lines.append("| Mod ID | Title | Phase | Est Data Ready | With Slack |")
        lines.append("|--------|-------|-------|----------------|------------|")
        for m in self.mods:
            dt = datetime.fromisoformat(m["est_data_ready"])
            slack = self.config.get("default_mod_lead_time_months", 0)
            dt_slack = dt + relativedelta(months=slack)
            lines.append(
                f"| {m['id']} | {m['title']} | {m['phase']} | "
                f"{dt.strftime('%Y-%m-%d')} | {dt_slack.strftime('%Y-%m-%d')} |"
            )
        return "\n".join(lines)
