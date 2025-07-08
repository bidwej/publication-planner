# src/plot.py

from __future__ import annotations
from typing import Dict
import matplotlib.pyplot as plt

from src.planner import Planner
from src.type import SubmissionType

def plot_schedule(
    planner: Planner,
    schedule: Dict[str, int],
    save_path: str = None
) -> None:
    """
    Plot a Gantt chart of the given schedule.

    Parameters
    ----------
    planner : Planner
        Planner instance containing submissions and timeline info.
    schedule : Dict[str, int]
        Dict of submission_id → start month index.
    save_path : str, optional
        If provided, saves the figure to a PNG instead of showing it interactively.
    """

    fig, ax = plt.subplots(figsize=(12, max(4, len(schedule) * 0.4)))

    y_labels = []
    y_positions = []

    for idx, sid in enumerate(sorted(schedule.keys())):
        s = planner.sub_map[sid]
        start_idx = schedule[sid]
        y_labels.append(sid)
        y_positions.append(idx)

        if s.kind == SubmissionType.PAPER:
            # Plot a horizontal bar
            ax.barh(
                y=idx,
                width=s.draft_window_months,
                left=start_idx,
                height=0.5,
                color="steelblue",
                edgecolor="black",
                label="Paper" if idx == 0 else None
            )
        elif s.kind == SubmissionType.ABSTRACT:
            # Plot a diamond marker
            ax.scatter(
                [start_idx],
                [idx],
                marker="D",
                color="darkorange",
                edgecolors="black",
                s=100,
                label="Abstract" if idx == 0 else None
            )
        else:
            # Plot mod milestone if desired (treated as paper now)
            ax.scatter(
                [start_idx],
                [idx],
                marker="o",
                color="green",
                edgecolors="black",
                s=80,
                label="Mod" if idx == 0 else None
            )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)

    xticks = list(range(len(planner.months)))
    xticklabels = [m.strftime("%Y-%m") for m in planner.months]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=45, ha="right", fontsize=8)

    ax.set_xlabel("Month")
    ax.set_title("Plausible Schedule Gantt Chart")

    # Add a legend without duplicates
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys())

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=200)
        print(f"Saved Gantt chart to: {save_path}")
    else:
        plt.show()
