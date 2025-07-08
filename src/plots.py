# src/plot.py

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt

from src.type import Submission, SubmissionType

def plot_schedule(
    schedule: Dict[str, int],
    submissions: List[Submission],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    save_path: Optional[str] = None
) -> None:
    """
    Plot a Gantt chart of the given schedule.

    Parameters
    ----------
    schedule : Dict[str, int]
        Maps submission_id → start month index
    submissions : List[Submission]
        List of all Submission objects
    start_date : date, optional
        If provided, crops timeline before this date.
    end_date : date, optional
        If provided, crops timeline after this date.
    save_path : str, optional
        If given, saves PNG instead of showing interactively.
    """

    subs = {s.id: s for s in submissions}

    months = _rebuild_months(
        schedule=schedule,
        subs=subs,
        start_date=start_date,
        end_date=end_date,
    )

    fig, ax = plt.subplots(figsize=(12, max(4, len(schedule) * 0.4)))

    y_labels: List[str] = []
    y_positions: List[int] = []

    for idx, sid in enumerate(sorted(schedule.keys())):
        s = subs[sid]
        start_idx = schedule[sid]

        # Skip items outside cropped view
        if start_idx >= len(months):
            continue

        y_labels.append(sid)
        y_positions.append(idx)

        if s.kind == SubmissionType.PAPER:
            ax.barh(
                y=idx,
                width=s.draft_window_months,
                left=start_idx,
                height=0.5,
                color="steelblue",
                edgecolor="black",
                label="Paper" if idx == 0 else None
            )
        else:
            ax.scatter(
                [start_idx],
                [idx],
                marker="D",
                color="darkorange",
                edgecolors="black",
                s=100,
                label="Abstract" if idx == 0 else None
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)

    xticks = list(range(len(months)))
    xticklabels = [m.strftime("%Y-%m") for m in months]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=45, ha="right", fontsize=8)

    ax.set_xlabel("Month")
    ax.set_title("Plausible Schedule Gantt Chart")

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys())

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200)
        print(f"Saved Gantt chart to: {save_path}")
    else:
        plt.show()


def _rebuild_months(
    schedule: Dict[str, int],
    subs: Dict[str, Submission],
    start_date: Optional[date],
    end_date: Optional[date],
) -> List[datetime]:
    """
    Compute the month grid needed for the Gantt chart.
    """

    if not schedule:
        return []

    # Find earliest internal_ready_date among all submissions
    earliest_date = min(
        s.internal_ready_date for s in subs.values()
    )
    start_dt = datetime(earliest_date.year, earliest_date.month, 1)

    # Find furthest month in the schedule
    latest_idx = max(
        schedule[sid] + subs[sid].draft_window_months
        for sid in schedule
    )
    total_months = latest_idx

    months: List[datetime] = []
    cur = start_dt
    for _ in range(total_months + 1):
        months.append(cur)
        cur += relativedelta(months=1)

    # Crop if user requests
    if start_date:
        months = [m for m in months if m.date() >= start_date]
    if end_date:
        months = [m for m in months if m.date() <= end_date]

    return months
