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

# ────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────
def load_config(config_path: str) -> Config:
    """Load the master config and all child JSON files."""
    with open(config_path, "r", encoding="utf-8") as f:
        raw_cfg = json.load(f)

    conferences = _load_conferences(raw_cfg["data_files"]["conferences"])
    submissions = _load_submissions(
        mods_path=raw_cfg["data_files"]["mods"],
        papers_path=raw_cfg["data_files"]["papers"],
        conferences=conferences,
        abs_lead=raw_cfg["min_abstract_lead_time_days"],
        pap_lead=raw_cfg["min_paper_lead_time_days"],
    )

    return Config(
        min_abstract_lead_time_days=raw_cfg["min_abstract_lead_time_days"],
        min_paper_lead_time_days=raw_cfg["min_paper_lead_time_days"],
        max_concurrent_submissions=raw_cfg["max_concurrent_submissions"],
        conferences=conferences,
        submissions=submissions,
        data_files=raw_cfg["data_files"],
    )

# ────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────
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

    for m in raw_mods:
        m_id = int(m["id"])
        subs.append(
            Submission(
                id=f"mod{m_id:02d}-wrk",
                kind=SubmissionType.PAPER,
                title=m["title"],
                earliest_start_date=_parse_date(m["est_data_ready"]),
                conference_id=None,
                engineering=True,
                depends_on=[f"mod{m_id-1:02d}-wrk"] if m_id > 1 else [],
                penalty_cost_per_day=((m["penalty_cost_per_month"] or 0) / 30),
            )
        )

    # ── Scientific Papers ──
    with open(papers_path, "r", encoding="utf-8") as f:
        raw_papers = json.load(f)

    for p in raw_papers:
        # Choose conference (optional)
        conf_name = (
            p.get("planned_conference")
            or (p["conference_families"][0] if p["conference_families"] else None)
        )
        conf_obj: Optional[Conference] = conf_map.get(conf_name) if conf_name else None

        abs_deadline = conf_obj.deadlines.get(SubmissionType.ABSTRACT) if conf_obj else None
        pap_deadline = conf_obj.deadlines.get(SubmissionType.PAPER) if conf_obj else None

        mod_deps = [f"mod{mid:02d}-wrk" for mid in p["mod_dependencies"]]
        parent_deps = [f"{pid}-pap" for pid in p["parent_papers"]]

        engineering = (
            conf_obj.conf_type == ConferenceType.ENGINEERING if conf_obj else True
        )

        # ---------- Optional abstract ----------
        abs_id = None
        if abs_deadline:
            abs_id = f"{p['id']}-abs"
            subs.append(
                Submission(
                    id=abs_id,
                    kind=SubmissionType.ABSTRACT,
                    title=f"{p['title']} (abstract)",
                    earliest_start_date=abs_deadline,   # zero-day task
                    conference_id=conf_obj.id,
                    engineering=engineering,
                    depends_on=mod_deps + parent_deps,
                )
            )

        # ---------- Full paper (if any deadline) ----------
        deadline = pap_deadline or abs_deadline
        if deadline:
            lead_days = pap_lead
            start_date = deadline - relativedelta(days=lead_days)

            subs.append(
                Submission(
                    id=f"{p['id']}-pap",
                    kind=SubmissionType.PAPER,
                    title=p["title"],
                    earliest_start_date=start_date,
                    conference_id=conf_obj.id if conf_obj else None,
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
