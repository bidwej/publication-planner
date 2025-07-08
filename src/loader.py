from __future__ import annotations
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from src.type import (
    Config,
    Conference,
    ConferenceType,
    Submission,
    SubmissionType,
)

def load_config(config_path: str) -> Config:
    # Loads the entire config, including separate JSON files.
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)

    confs = _load_conferences(raw_config["data_files"]["conferences"])
    subs = _load_submissions(
        mods_path=raw_config["data_files"]["mods"],
        papers_path=raw_config["data_files"]["papers"],
        conferences=confs,
    )

    return Config(
        default_lead_time_days=raw_config["default_paper_lead_time_days"],
        max_concurrent_submissions=raw_config["max_concurrent_submissions"],
        slack_window_days=raw_config["default_mod_lead_time_days"],
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
) -> List[Submission]:
    conf_map = {c.id: c for c in conferences}
    subs: List[Submission] = []

    # Dynamically build set of engineering conferences
    ENGINEERING_CONFERENCES = {
        c.id for c in conferences if c.conf_type == ConferenceType.ENGINEERING
    }

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
                min_draft_window_days=None,  # mods have no draft window
                engineering=True,
                depends_on=[
                    f"mod{int(m['id'])-1:02d}-wrk"
                ] if int(m["id"]) > 1 else [],
                free_slack_days=m["free_slack_months"] * 30,
                penalty_cost_per_day=m["penalty_cost_per_month"] / 30
                if m["penalty_cost_per_month"] else 0,
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

        # Determine engineering from conference type
        engineering = True
        if conf_name and conf_name in conf_map:
            conf_type = conf_map[conf_name].conf_type
            engineering = conf_type == ConferenceType.ENGINEERING

        abs_id = None
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
                    min_draft_window_days=0,
                    engineering=engineering,
                    depends_on=mod_deps + parent_deps,
                )
            )

        paper_id = f"{p['id']}-pap"
        depends = mod_deps + parent_deps
        if abs_id:
            depends.append(abs_id)

        if pap_deadline or abs_deadline:
            deadline = pap_deadline or abs_deadline

            draft_window_days = None
            if "draft_window_months" in p and p["draft_window_months"] is not None:
                draft_window_days = int(p["draft_window_months"] * 30)

            subs.append(
                Submission(
                    id=paper_id,
                    kind=SubmissionType.PAPER,
                    title=p["title"],
                    internal_ready_date=deadline,
                    external_due_date=deadline,
                    conference_id=conf_obj.id if conf_obj else None,
                    min_draft_window_days=draft_window_days,
                    engineering=engineering,
                    depends_on=depends,
                )
            )
    return subs

def _parse_date(d: str) -> date:
    clean = d.split("T")[0]
    try:
        return datetime.fromisoformat(clean).date()
    except ValueError as exc:
        raise ValueError(
            f"Invalid date format: {d}. Expected YYYY-MM-DD."
        ) from exc
