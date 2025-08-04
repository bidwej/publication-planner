# src/output/plots.py
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date, datetime
from dateutil.relativedelta import relativedelta  # type: ignore
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches  # type: ignore
from core.types import Submission, SubmissionType, Config


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

    fig, ax = plt.subplots(figsize=(14, max(6, len(schedule) * 0.4)))  # type: ignore

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
    if (
        config
        and config.scheduling_options
        and config.scheduling_options.get("enable_blackout_periods", False)
        and config.blackout_dates
    ):
        for blackout_date in config.blackout_dates:
            if min_date <= blackout_date <= max_date:
                ax.axvline(
                    x=(blackout_date - min_date).days,
                    color="red",
                    alpha=0.3,
                    linestyle="--",
                )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Days from start")
    ax.set_title("Schedule Gantt Chart")
    ax.grid(True, alpha=0.3)

    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="upper right")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        plt.show()


def _get_priority_color(sub: Submission, config: Optional[Config]) -> str:
    """Get color based on submission priority."""
    if not config or not config.priority_weights:
        return "blue"
    
    weights = config.priority_weights
    if sub.kind == SubmissionType.PAPER:
        if sub.engineering:
            priority = weights.get("engineering_paper", 2.0)
        else:
            priority = weights.get("medical_paper", 1.0)
    elif sub.kind == SubmissionType.ABSTRACT:
        priority = weights.get("abstract", 0.5)
    else:
        priority = weights.get("mod", 1.5)
    
    if priority >= 2.0:
        return "red"
    elif priority >= 1.5:
        return "orange"
    elif priority >= 1.0:
        return "yellow"
    else:
        return "green"


def _get_label(sub: Submission, idx: int) -> Optional[str]:
    """Get label for legend."""
    if idx == 0:
        return f"{sub.kind.value} ({'Engineering' if sub.engineering else 'Medical'})"
    return None


def plot_utilization_chart(schedule: Dict[str, date], config: Config, save_path: Optional[str] = None) -> None:
    """Plot resource utilization over time."""
    if not schedule:
        return
    
    # Calculate daily utilization
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day
        for i in range(duration + 1):
            day = start_date + relativedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    if not daily_load:
        return
    
    # Convert to lists for plotting
    dates = sorted(daily_load.keys())
    loads = [daily_load[date] for date in dates]
    utilizations = [load / config.max_concurrent_submissions for load in loads]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(dates, utilizations, 'b-', linewidth=2, alpha=0.7)
    ax.fill_between(dates, utilizations, alpha=0.3, color='blue')
    
    # Add threshold lines
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Max Capacity')
    ax.axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='80% Capacity')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Resource Utilization')
    ax.set_title('Resource Utilization Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        plt.show()


def plot_deadline_compliance(schedule: Dict[str, date], config: Config, save_path: Optional[str] = None) -> None:
    """Plot deadline compliance information."""
    if not schedule:
        return
    
    # Calculate deadline information
    deadlines = []
    margins = []
    labels = []
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
            end_date = start_date + relativedelta(days=duration)
        else:
            end_date = start_date
        
        margin = (deadline - end_date).days
        
        deadlines.append(deadline)
        margins.append(margin)
        labels.append(f"{sid}\n{sub.title[:20]}...")
    
    if not deadlines:
        return
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Color code by margin
    colors = ['red' if m < 0 else 'green' if m > 30 else 'orange' for m in margins]
    
    bars = ax.barh(range(len(deadlines)), margins, color=colors, alpha=0.7)
    
    # Add deadline lines
    for i, deadline in enumerate(deadlines):
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
    
    ax.set_yticks(range(len(deadlines)))
    ax.set_yticklabels(labels)
    ax.set_xlabel('Margin (days) - Negative = Late')
    ax.set_title('Deadline Compliance')
    ax.grid(True, alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', alpha=0.7, label='On Time (>30 days)'),
        Patch(facecolor='orange', alpha=0.7, label='Close (<30 days)'),
        Patch(facecolor='red', alpha=0.7, label='Late')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
    else:
        plt.show() 