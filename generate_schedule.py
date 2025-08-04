#!/usr/bin/env python3
# generate_schedule.py
from __future__ import annotations

import sys
import platform
import argparse
from datetime import datetime

from loader import load_config
from scheduler import greedy_schedule, save_schedule
from plots import plot_schedule



def generate_schedule_cli() -> None:
    parser = argparse.ArgumentParser(description="Endoscope AI Scheduling Tool")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    parser.add_argument("--start-date", type=str, help="Crop Gantt chart start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="Crop Gantt chart end date (YYYY-MM-DD)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    while True:
        # Generate schedule
        schedule = greedy_schedule(cfg)

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
            print("Regenerating a new schedule...")
            continue
        elif key in ("\r", "\n"):
            out_path = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_schedule(schedule, cfg.submissions, out_path)
            break
        elif key.lower() == "q" or key == "\x1b":
            print("Exiting without saving.")
            break
        else:
            print(f"Unknown key: {repr(key)} → quitting.")
            break


# --------------------- Internals -------------------------

def _parse_date(d: str | None) -> None | datetime.date:
    # Parse a date string or return None
    if d is None:
        return None
    clean = d.split("T")[0]
    try:
        return datetime.fromisoformat(clean).date()
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {d}. Expected YYYY-MM-DD.") from exc


def _prompt_keypress() -> str:
    # Cross-platform keypress prompt
    print("")
    print("Press SPACE to regenerate, ENTER to save schedule, or Q / ESC to quit.")
    print(">", end=" ", flush=True)

    try:
        if platform.system() == "Windows":
            import msvcrt
            return msvcrt.getwch()
        else:
            import termios  # pylint: disable=import-error, import-outside-toplevel
            import tty      # pylint: disable=import-error, import-outside-toplevel
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                return sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        print(f"\n[Warning] Unable to read keypress: {e}")
        return "\n"  # Default to "ENTER" behavior


if __name__ == "__main__":
    generate_schedule_cli()
