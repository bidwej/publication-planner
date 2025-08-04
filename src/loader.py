from __future__ import annotations

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta

from type import (
    Config,
    Conference,
    ConferenceType,
    Submission,
    SubmissionType,
)


# ────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────
def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = json.load(f)
    config_dir = os.path.dirname(os.path.abspath(config_path))

    conferences = _load_conferences(os.path.join(config_dir, raw_cfg["data_files"]["conferences"]))
    submissions = _load_submissions(
        mods_path=os.path.join(config_dir, raw_cfg["data_files"]["mods"]),
        papers_path=os.path.join(config_dir, raw_cfg["data_files"]["papers"]),
        conferences=conferences,
        abs_lead=raw_cfg["min_abstract_lead_time_days"],
        pap_lead=raw_cfg["min_paper_lead_time_days"],
        penalty_costs=raw_cfg.get("penalty_costs", {}),
    )

    # Load blackout dates if enabled
    blackout_dates = []
    if raw_cfg.get("scheduling_options", {}).get("enable_blackout_periods", False):
        blackouts_rel = raw_cfg["data_files"].get("blackouts")
        if blackouts_rel:
            blackout_path = os.path.join(config_dir, blackouts_rel)
            blackout_dates = _load_blackout_dates(blackout_path)

    return Config(
        min_abstract_lead_time_days=raw_cfg["min_abstract_lead_time_days"],
        min_paper_lead_time_days=raw_cfg["min_paper_lead_time_days"],
        max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
        mod_to_paper_gap_days=raw_cfg["mod_to_paper_gap_days"],
        paper_parent_gap_days=raw_cfg.get("paper_parent_gap_days", 90),
        conferences=conferences,
        submissions=submissions,
        data_files=raw_cfg["data_files"],
        priority_weights=raw_cfg.get(
            "priority_weights",
            {
                "engineering_paper": 2.0,
                "medical_paper": 1.0,
                "mod": 1.5,
                "abstract": 0.5,
            },
        ),
        penalty_costs=raw_cfg.get(
            "penalty_costs", {"default_mod_penalty_per_day": 1000}
        ),
        scheduling_options=raw_cfg.get("scheduling_options", {}),
        blackout_dates=blackout_dates,
    )


# ────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────
def _load_blackout_dates(path: str) -> List[date]:
    """Load blackout dates from JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        blackout_dates = []

        # Add federal holidays
        for year_key in ["federal_holidays_2025", "federal_holidays_2026"]:
            if year_key in raw:
                for date_str in raw[year_key]:
                    blackout_dates.append(_parse_date(date_str))

        # Add custom blackout periods
        if "custom_blackout_periods" in raw:
            for period in raw["custom_blackout_periods"]:
                start = _parse_date(period["start"])
                end = _parse_date(period["end"])
                current = start
                while current <= end:
                    blackout_dates.append(current)
                    current += relativedelta(days=1)

        return blackout_dates
    except Exception as e:
        print(f"Warning: Could not load blackout dates: {e}")
        return []


def _load_conferences(path: str) -> List[Conference]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    out: List[Conference] = []
    for c in raw:
        deadlines: Dict[SubmissionType, date] = {}
        if c.get("abstract_deadline"):
            deadlines[SubmissionType.ABSTRACT] = _parse_date(c["abstract_deadline"])
        if c.get("full_paper_deadline"):
            deadlines[SubmissionType.PAPER] = _parse_date(c["full_paper_deadline"])

        out.append(
            Conference(
                id=c["name"],
                conf_type=ConferenceType(c["conference_type"]),
                recurrence=c["recurrence"],
                deadlines=deadlines,
            )
        )
    return out


def _load_submissions(
    mods_path: str,
    papers_path: str,
    conferences: List[Conference],
    abs_lead: int,
    pap_lead: int,
    penalty_costs: Dict[str, float],
) -> List[Submission]:
    """
    Build all Submission objects for mods and papers.
    No per-submission draft window exists any more; we rely on the
    global lead times (`abs_lead`, `pap_lead`).
    """
    conf_map = {c.id: c for c in conferences}
    subs: List[Submission] = []

    # ── PCCP / FDA Mods (treated as PAPER-length tasks) ──
    with open(mods_path, "r", encoding="utf-8") as f:
        raw_mods = json.load(f)

    default_mod_penalty = penalty_costs.get("default_mod_penalty_per_day", 1000)

    for m in raw_mods:
        m_id = int(m["id"])
        # Use specific penalty if provided, otherwise use default
        penalty_per_month = m.get("penalty_cost_per_month", default_mod_penalty * 30)

        subs.append(
            Submission(
                id=f"mod{m_id:02d}-wrk",
                kind=SubmissionType.PAPER,
                title=m["title"],
                earliest_start_date=_parse_date(m["est_data_ready"]),
                conference_id=None,
                engineering=True,
                depends_on=[f"mod{m_id-1:02d}-wrk"] if m_id > 1 else [],
                penalty_cost_per_day=(penalty_per_month / 30),
            )
        )

    # ── Scientific Papers ──
    with open(papers_path, "r", encoding="utf-8") as f:
        raw_papers = json.load(f)

    for p in raw_papers:
        # Choose conference (optional)
        conf_name = p.get("planned_conference") or (
            p["conference_families"][0] if p["conference_families"] else None
        )
        conf_obj: Optional[Conference] = conf_map.get(conf_name) if conf_name else None

        abs_deadline = (
            conf_obj.deadlines.get(SubmissionType.ABSTRACT) if conf_obj else None
        )
        pap_deadline = (
            conf_obj.deadlines.get(SubmissionType.PAPER) if conf_obj else None
        )

        mod_deps = [f"mod{mid:02d}-wrk" for mid in p["mod_dependencies"]]
        parent_deps = [f"{pid}-pap" for pid in p["parent_papers"]]

        # Determine if engineering based on paper type
        paper_type = p.get("paper_type", "engineering").lower()
        engineering = paper_type == "engineering"

        # ---------- Optional abstract ----------
        abs_id = None
        if abs_deadline:
            abs_id = f"{p['id']}-abs"
            subs.append(
                Submission(
                    id=abs_id,
                    kind=SubmissionType.ABSTRACT,
                    title=f"{p['title']} (abstract)",
                    earliest_start_date=abs_deadline,  # zero-day task
                    conference_id=conf_obj.id if conf_obj is not None else None,
                    engineering=engineering,
                    depends_on=mod_deps + parent_deps,
                )
            )

        # ---------- Full paper (if any deadline) ----------
        deadline = pap_deadline or abs_deadline
        if deadline:
            lead_days = pap_lead
            start_date = deadline - relativedelta(days=lead_days)
            
            # Ensure start date is not in the past relative to the earliest deadline
            # Find the earliest deadline across all conferences (only 2025+ deadlines)
            all_deadlines = []
            for conf in conferences:
                for dl in conf.deadlines.values():
                    if dl.year >= 2025:  # Only consider 2025+ deadlines
                        all_deadlines.append(dl)
            if all_deadlines:
                earliest_deadline = min(all_deadlines)
                earliest_allowed = earliest_deadline - relativedelta(days=30)
                start_date = max(start_date, earliest_allowed)

            subs.append(
                Submission(
                    id=f"{p['id']}-pap",
                    kind=SubmissionType.PAPER,
                    title=p["title"],
                    earliest_start_date=start_date,
                    conference_id=conf_obj.id if conf_obj is not None else None,
                    engineering=engineering,
                    depends_on=mod_deps + parent_deps + ([abs_id] if abs_id else []),
                )
            )

    return subs


# ────────────────────────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────────────────────────
def _parse_date(d: str) -> date:
    try:
        return datetime.fromisoformat(d.split("T")[0]).date()
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {d!r}") from exc
