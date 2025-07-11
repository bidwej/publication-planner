# src/plots.py

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from src.type import Submission, SubmissionType, Config


def plot_schedule(
    schedule: Dict[str, date],
    submissions: List[Submission],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    save_path: Optional[str] = None,
    config: Optional[Config] = None,
) -> None:
    """
    Plot a Gantt chart of the given schedule.

    Parameters
    ----------
    schedule : Dict[str, date]
        Maps submission_id → start date
    submissions : List[Submission]
        List of all Submission objects
    start_date : date, optional
        If provided, crops timeline before this date.
    end_date : date, optional
        If provided, crops timeline after this date.
    save_path : str, optional
        If given, saves PNG instead of showing interactively.
    config : Config, optional
        Configuration for blackout dates and priority colors
    """

    subs = {s.id: s for s in submissions}

    # Convert schedule to daily grid
    all_dates = list(schedule.values())
    if not all_dates:
        return

    min_date = min(all_dates)
    max_date = max(all_dates) + relativedelta(days=90)  # Show 3 months beyond

    # Apply cropping
    if start_date:
        min_date = max(min_date, start_date)
    if end_date:
        max_date = min(max_date, end_date)

    fig, ax = plt.subplots(figsize=(14, max(6, len(schedule) * 0.4)))

    y_labels: List[str] = []
    y_positions: List[int] = []

    for idx, sid in enumerate(sorted(schedule.keys())):
        s = subs[sid]
        start = schedule[sid]

        # Skip items outside view
        if start > max_date or start < min_date:
            continue

        y_labels.append(f"{sid} - {s.title[:40]}...")
        y_positions.append(idx)

        # Determine color based on priority
        color = _get_priority_color(s, config)

        if s.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days if config else 60
            ax.barh(
                y=idx,
                width=duration,
                left=(start - min_date).days,
                height=0.6,
                color=color,
                edgecolor="black",
                alpha=0.8,
                label=_get_label(s, idx),
            )
        else:  # Abstract
            ax.scatter(
                [(start - min_date).days],
                [idx],
                marker="D",
                color=color,
                edgecolors="black",
                s=100,
                alpha=0.8,
                label="Abstract" if idx == 0 else None,
            )

    # Show blackout periods
    if config and config.scheduling_options.get("enable_blackout_periods", False):
        for blackout in config.blackout_dates:
            if min_date <= blackout <= max_date:
                ax.axvline(
                    x=(blackout - min_date).days, color="red", alpha=0.2, linewidth=1
                )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=8)

    # X-axis setup
    total_days = (max_date - min_date).days
    month_ticks = []
    month_labels = []

    current = min_date.replace(day=1)
    while current <= max_date:
        tick_pos = (current - min_date).days
        if tick_pos >= 0:
            month_ticks.append(tick_pos)
            month_labels.append(current.strftime("%Y-%m"))
        current += relativedelta(months=1)

    ax.set_xticks(month_ticks)
    ax.set_xticklabels(month_labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlim(0, total_days)

    ax.set_xlabel("Date")
    ax.set_title("Endoscope AI Schedule Gantt Chart")
    ax.grid(True, axis="x", alpha=0.3)

    # Legend
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), loc="upper right", fontsize=8)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"Saved Gantt chart to: {save_path}")
    else:
        plt.show()


def _get_priority_color(sub: Submission, config: Optional[Config]) -> str:
    """Get color based on submission priority."""
    if not config or not config.priority_weights:
        return "steelblue"

    if sub.kind == SubmissionType.ABSTRACT:
        return "darkorange"
    elif sub.conference_id is None:  # Mod
        return "darkgreen"
    elif sub.engineering:
        return "steelblue"
    else:  # Medical
        return "mediumpurple"


def _get_label(sub: Submission, idx: int) -> Optional[str]:
    """Get legend label for first occurrence of each type."""
    if idx != 0:
        return None

    if sub.conference_id is None:
        return "PCCP Mod"
    elif sub.engineering:
        return "Engineering Paper"
    else:
        return "Medical Paper"
