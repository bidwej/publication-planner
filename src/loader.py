from __future__ import annotations
import json
from datetime import datetime, date
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta

from src.type import (
    Config,
    Conference,
    ConferenceType,
    Submission,
    SubmissionType,
)


# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────
def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = json.load(f)

    conferences = _load_conferences(raw_cfg["data_files"]["conferences"])
    submissions = _load_submissions(
        mods_path=raw_cfg["data_files"]["mods"],
        papers_path=raw_cfg["data_files"]["papers"],
        conferences=conferences,
        slack_days=raw_cfg["default_mod_lead_time_days"],
        default_paper_lead_days=raw_cfg["default_paper_lead_time_days"],
    )

    return Config(
        default_lead_time_days=raw_cfg["default_paper_lead_time_days"],
        max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
        slack_window_days=raw_cfg["default_mod_lead_time_days"],
        conferences=conferences,
        submissions=submissions,
        data_files=raw_cfg["data_files"],
    )


# ────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────
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
    *,
    slack_days: int,
    default_paper_lead_days: int,
) -> List[Submission]:
    """Create Submission objects for mods + papers."""
    conf_map = {c.id: c for c in conferences}
    subs: List[Submission] = []

    # ---------- Mods ----------
    with open(mods_path, "r", encoding="utf-8") as f:
        raw_mods = json.load(f)

    for m in raw_mods:
        subs.append(
            Submission(
                id=f"mod{int(m['id']):02d}-wrk",
                kind=SubmissionType.PAPER,
                title=m["title"],
                earliest_start_date=_parse_date(m["est_data_ready"]),
                conference_id=None,
                min_draft_window_days=None,          # mods draft instantly
                engineering=True,
                depends_on=[
                    f"mod{int(m['id'])-1:02d}-wrk"
                ] if int(m["id"]) > 1 else [],
                free_slack_days=m["free_slack_months"] * 30,
                penalty_cost_per_day=(
                    m["penalty_cost_per_month"] / 30
                    if m["penalty_cost_per_month"] else 0
                ),
            )
        )

    # ---------- Papers ----------
    with open(papers_path, "r", encoding="utf-8") as f:
        raw_papers = json.load(f)

    for p in raw_papers:
        # Pick a conference
        conf_name = (
            p.get("planned_conference")
            or (p["conference_families"][0] if p["conference_families"] else None)
        )
        conf_obj: Optional[Conference] = conf_map.get(conf_name) if conf_name else None

        # Deadlines
        abs_deadline = conf_obj.deadlines.get(SubmissionType.ABSTRACT) if conf_obj else None
        pap_deadline = conf_obj.deadlines.get(SubmissionType.PAPER) if conf_obj else None

        # Dependencies
        mod_deps = [f"mod{mid:02d}-wrk" for mid in p["mod_dependencies"]]
        parent_deps = [f"{pid}-pap" for pid in p["parent_papers"]]

        # Determine engineering flag from conference
        engineering = (
            conf_obj.conf_type == ConferenceType.ENGINEERING
            if conf_obj else True
        )

        # --- Abstract submission (optional) ---
        abs_id = None
        if abs_deadline:
            abs_id = f"{p['id']}-abs"
            subs.append(
                Submission(
                    id=abs_id,
                    kind=SubmissionType.ABSTRACT,
                    title=f\"{p['title']} (abstract)\",
                    earliest_start_date=abs_deadline,   # zero-day task
                    conference_id=conf_obj.id,
                    min_draft_window_days=0,
                    engineering=engineering,
                    depends_on=mod_deps + parent_deps,
                )
            )

        # --- Full paper submission (optional) ---
        if pap_deadline or abs_deadline:
            deadline = pap_deadline or abs_deadline

            draft_window_days = (
                int(p["draft_window_months"] * 30)
                if p.get("draft_window_months") is not None
                else default_paper_lead_days
            )

            # Earliest start = deadline minus drafting window minus global slack
            start_date = deadline - relativedelta(days=draft_window_days + slack_days)

            paper_id = f"{p['id']}-pap"
            depends = mod_deps + parent_deps + ([abs_id] if abs_id else [])

            subs.append(
                Submission(
                    id=paper_id,
                    kind=SubmissionType.PAPER,
                    title=p["title"],
                    earliest_start_date=start_date,
                    conference_id=conf_obj.id if conf_obj else None,
                    min_draft_window_days=draft_window_days,
                    engineering=engineering,
                    depends_on=depends,
                )
            )

    return subs


# ────────────────────────────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────────────────────────────
def _parse_date(d: str) -> date:
    """Convert ISO (YYYY-MM-DD or ISO-8601) to date, raise on failure."""
    try:
        return datetime.fromisoformat(d.split("T")[0]).date()
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {d}") from exc
