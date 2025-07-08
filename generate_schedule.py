#!/usr/bin/env python3
# generate_schedule.py

from __future__ import annotations
from datetime import datetime
import argparse
import json
import os
import sys

import matplotlib.pyplot as plt

from src.loader import load_config
from src.scheduler import greedy_schedule, solve_lp
from src.plots import plot_schedule

from src.type import Config, Submission

def generate_schedule_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Endoscope AI Scheduling Tool"
    )
    parser.add_argument(
        "--config", type=str, default="config.json",
        help="Path to config.json"
    )
    parser.add_argument(
        "--start-date", type=str,
        help="Crop Gantt chart start date (YYYY-MM)"
    )
    parser.add_argument(
        "--end-date", type=str,
        help="Crop Gantt chart end date (YYYY-MM)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    while True:
        # Generate schedule
        schedule = _run_scheduler(cfg, use_lp=args.lp)

        # Plot it
        plot_schedule(
            schedule=schedule,
            submissions=cfg.submissions,
            start_date=_parse_date(args.start_date),
            end_date=_parse_date(args.end_date),
            save_path=None
        )

        key = _prompt_keypress()

        if key == " ":
            # Space → regenerate
            print("Regenerating a new schedule...")
            continue
        elif key == "\r" or key == "\n":
            # Enter → save
            _save_schedule(schedule, cfg.submissions)
            break
        elif key.lower() == "q":
            print("Exiting without saving.")
            break
        else:
            print(f"Unknown key: {repr(key)} → quitting.")
            break


# --------------------- Internals -------------------------

def _run_scheduler(cfg: Config, use_lp: bool) -> dict[str, int]:
    """
    Run either greedy or LP scheduling and return:
        {submission_id: start_month_index}
    """
    if use_lp:
        fractional = solve_lp(cfg)
        # round to int month indices
        return {k: int(round(v)) for k, v in fractional.items()}
    else:
        return greedy_schedule(cfg)


def _parse_date(d: str | None) -> None | datetime.date:
    """
    Parse YYYY-MM string to date. None → None.
    """
    if d is None:
        return None
    try:
        return datetime.strptime(d, "%Y-%m").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {d}. Expected YYYY-MM.")


def _prompt_keypress() -> str:
    """
    Prompt for a single keypress. Supports:
      - SPACE → regenerate
      - ENTER → save
      - q → quit
    """
    print("")
    print("Press SPACE to regenerate, ENTER to save schedule, or Q to quit.")
    print(">", end=" ", flush=True)

    # platform-agnostic read
    try:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    except ImportError:
        # Windows fallback
        import msvcrt
        return msvcrt.getwch()


def _save_schedule(
    schedule: dict[str, int],
    submissions: list[Submission]
) -> None:
    """
    Save the schedule + submission metadata to JSON in the working dir.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"schedule_{timestamp}.json"

    output = []
    for sid, start_idx in schedule.items():
        s = next(sub for sub in submissions if sub.id == sid)
        output.append({
            "id": s.id,
            "title": s.title,
            "kind": s.kind.value,
            "internal_ready_date": s.internal_ready_date.isoformat(),
            "external_due_date": s.external_due_date.isoformat() if s.external_due_date else None,
            "conference_id": s.conference_id,
            "draft_window_months": s.draft_window_months,
            "engineering": s.engineering,
            "depends_on": s.depends_on,
            "start_month_index": start_idx,
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Schedule saved to {out_path}")


if __name__ == "__main__":
    generate_schedule_cli()
