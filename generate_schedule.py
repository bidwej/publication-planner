#!/usr/bin/env python3
# generate_schedule.py
from __future__ import annotations
import sys
import platform
import argparse
import os
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import load_config
from core.dates import parse_date
from schedulers.greedy import GreedyScheduler
from output.plots import plot_schedule

def generate_schedule_cli() -> None:
    parser = argparse.ArgumentParser(description="Endoscope AI Scheduling Tool")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config.json")
    parser.add_argument("--start-date", type=str, help="Crop Gantt chart start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="Crop Gantt chart end date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    config = load_config(args.config)
    scheduler = GreedyScheduler(config)
    
    while True:
        # Generate schedule
        schedule = scheduler.schedule()
        
        # Plot it
        plot_schedule(
            schedule=schedule,
            submissions=config.submissions,
            start_date=parse_date(args.start_date),
            end_date=parse_date(args.end_date),
            save_path=None
        )
        
        key = _prompt_keypress()
        if key == " ":
            print("Regenerating a new schedule...")
            continue
        elif key in ("\r", "\n"):
            out_path = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            # Save schedule using the new structure
            import json
            with open(out_path, 'w') as f:
                json.dump(schedule, f, default=str, indent=2)
            print(f"Schedule saved to: {out_path}")
            break
        elif key.lower() == "q" or key == "\x1b":
            print("Exiting without saving.")
            break
        else:
            print(f"Unknown key: {repr(key)} → quitting.")
            break



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