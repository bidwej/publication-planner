# src/loader.py

from __future__ import annotations
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from type import (
    Config,
    Conference,
    ConferenceType,
    Submission,
    SubmissionType,
)

def load_config(config_path: str) -> Config:
    """
    Loads the entire config, including separate JSON files.
    Returns
    -------
    Config
    """
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)

    confs = _load_conferences(raw_config["data_files"]["conferences"])
    subs = _load_submissions(
        mods_path=raw_config["data_files"]["mods"],
        papers_path=raw_config["data_files"]["papers"],
        conferences=confs,
    )

    return Config(
        default_lead_time_months=raw_config["default_paper_lead_time_months"],
        max_concurrent_submissions=raw_config["max_concurrent_papers"],
        slack_window_days=raw_config["default_mod_lead_time_months"] * 30,
        conferences=confs,
        submissions=subs,
        data_files=raw_config["data_files"],
    )

# --------------------------------------------------------------------------
# Private loaders
# --------------------------------------------------------------------------

def _load_conferences(path: str) -> List[Conference]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    out: List[Conference] = []
    for c in raw:
        deadlines = {}
        if c.get("abstract_deadline"):
            deadlines[SubmissionType.ABSTRACT] = _parse_date(c["abstract_deadline"])
        if c.get("full_paper_deadline"):
            deadlines[SubmissionType.PAPER] = _parse_date(c["full_paper_deadline"])
        out.append(
            Conference(
                id=c["name"],
                conf_type=ConferenceType(c["venue_type"]),
                recurrence=c["recurrence"],
                deadlines=deadlines,
            )
        )
    return out

def _load_submissions(
    mods_path: str,
    papers_path: str,
    conferences: List[Conference],
) -> List[Submission]:
    """
    Combines mods + papers into a single list of Submission objects.
    """
    conf_map = {c.id: c for c in conferences}
    subs: List[Submission] = []

    # Load all mods first
    with open(mods_path, "r", encoding="utf-8") as f:
        raw_mods = json.load(f)

    for m in raw_mods:
        subs.append(
            Submission(
                id=f"mod{int(m['id']):02d}-wrk",
                kind=SubmissionType.PAPER,
                title=m["title"],
                internal_ready_date=_parse_date(m["est_data_ready"]),
                external_due_date=None,
                conference_id=None,
                draft_window_months=0,
                engineering=True,
                depends_on=[
                    f"mod{int(m['id'])-1:02d}-wrk"
                ] if int(m["id"]) > 1 else [],
                free_slack_months=m["free_slack_months"],
                penalty_cost_per_month=m["penalty_cost_per_month"],
            )
        )

    # Now load papers
    with open(papers_path, "r", encoding="utf-8") as f:
        raw_papers = json.load(f)

    for p in raw_papers:
        planned_conf = p.get("planned_conference")
        conf_name = planned_conf or (
            p["conference_families"][0] if p["conference_families"] else None
        )
        conf_obj: Optional[Conference] = conf_map.get(conf_name) if conf_name else None

        abs_deadline = None
        pap_deadline = None

        if conf_obj:
            abs_deadline = conf_obj.deadlines.get(SubmissionType.ABSTRACT)
            pap_deadline = conf_obj.deadlines.get(SubmissionType.PAPER)

        mod_deps = [f"mod{mid:02d}-wrk" for mid in p["mod_dependencies"]]
        parent_deps = [f"{pid}-pap" for pid in p["parent_papers"]]

        abs_id = None
        # If venue has an abstract deadline, create abstract Submission
        if abs_deadline:
            abs_id = f"{p['id']}-abs"
            subs.append(
                Submission(
                    id=abs_id,
                    kind=SubmissionType.ABSTRACT,
                    title=f"{p['title']} (abstract)",
                    internal_ready_date=abs_deadline,
                    external_due_date=abs_deadline,
                    conference_id=conf_obj.id if conf_obj else None,
                    draft_window_months=0,
                    engineering=p["engineering"],
                    depends_on=mod_deps + parent_deps,
                )
            )

        # Create paper submission row
        paper_id = f"{p['id']}-pap"
        depends = mod_deps + parent_deps
        if abs_id:
            depends.append(abs_id)

        if pap_deadline or abs_deadline:
            # choose paper deadline if it exists, else fall back to abstract deadline
            deadline = pap_deadline or abs_deadline
            subs.append(
                Submission(
                    id=paper_id,
                    kind=SubmissionType.PAPER,
                    title=p["title"],
                    internal_ready_date=deadline,
                    external_due_date=deadline,
                    conference_id=conf_obj.id if conf_obj else None,
                    draft_window_months=p["draft_window_months"],
                    engineering=p["engineering"],
                    depends_on=depends,
                )
            )
        # else no conference yet assigned → no paper row emitted

    return subs

def _parse_date(datestr: str) -> date:
    """
    Converts ISO string → datetime.date.
    """
    clean = datestr.split("T")[0]
    return datetime.fromisoformat(clean).date()
