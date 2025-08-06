"""Plot generation for schedules."""

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import date, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from core.models import Submission, SubmissionType, Config


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
    max_date = max(all_dates) + timedelta(days=90)  # Show 3 months beyond

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
            ax.axvline(
                x=(blackout_date - min_date).days,
                color="red",
                linestyle="--",
                alpha=0.5,
                label="Blackout" if blackout_date == config.blackout_dates[0] else None,
            )

    # Formatting
    ax.set_xlabel("Days from start")
    ax.set_ylabel("Submissions")
    ax.set_title("Schedule Gantt Chart")
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        plt.close()
    else:
        plt.show()


def _get_priority_color(sub: Submission, config: Optional[Config]) -> str:
    """Get color based on submission priority."""
    if not config or not config.priority_weights:
        return "lightblue"

    weights = config.priority_weights
    priority = weights.get(sub.id, 1.0)
    
    if priority >= 0.8:
        return "red"
    elif priority >= 0.6:
        return "orange"
    elif priority >= 0.4:
        return "yellow"
    else:
        return "lightblue"


def _get_label(sub: Submission, idx: int) -> Optional[str]:
    """Get label for legend."""
    return f"{sub.kind.value}" if idx == 0 else None


def plot_utilization_chart(schedule: Dict[str, date], config: Config, save_path: Optional[str] = None) -> None:
    """Plot resource utilization over time."""
    if not schedule:
        return

    # Calculate daily utilization
    daily_load = {}
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        duration = config.min_paper_lead_time_days
        if sub.kind == SubmissionType.ABSTRACT:
            duration = 0
        
        # Add load for each day
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1

    if not daily_load:
        return

    dates = sorted(daily_load.keys())
    loads = [daily_load[date] for date in dates]
    utilizations = [load / config.max_concurrent_submissions for load in loads]

    fig, ax = plt.subplots(figsize=(12, 6))  # type: ignore
    ax.plot(dates, utilizations, marker="o", linewidth=2, markersize=4)
    ax.axhline(y=1.0, color="red", linestyle="--", alpha=0.7, label="Capacity")
    ax.fill_between(dates, utilizations, alpha=0.3)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Utilization")
    ax.set_title("Resource Utilization Over Time")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.WeekLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        plt.close()
    else:
        plt.show()


def plot_deadline_compliance(schedule: Dict[str, date], config: Config, save_path: Optional[str] = None) -> None:
    """Plot deadline compliance information."""
    if not schedule:
        return

    # Calculate deadline compliance
    on_time = []
    late = []
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub or not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        duration = config.min_paper_lead_time_days
        if sub.kind == SubmissionType.ABSTRACT:
            duration = 0
        
        end_date = start_date + timedelta(days=duration)
        
        if end_date <= deadline:
            on_time.append(sub.title)
        else:
            days_late = (end_date - deadline).days
            late.append((sub.title, days_late))

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))  # type: ignore
    
    # Pie chart of compliance
    labels = ["On Time", "Late"]
    sizes = [len(on_time), len(late)]
    colors = ["lightgreen", "lightcoral"]
    
    if sum(sizes) > 0:
        ax1.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax1.set_title("Deadline Compliance")
    
    # Bar chart of days late
    if late:
        titles, days = zip(*late)
        ax2.bar(range(len(titles)), days, color="lightcoral")
        ax2.set_xlabel("Submissions")
        ax2.set_ylabel("Days Late")
        ax2.set_title("Days Late for Each Submission")
        ax2.set_xticks(range(len(titles)))
        ax2.set_xticklabels([t[:20] + "..." if len(t) > 20 else t for t in titles], rotation=45)
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        plt.close()
    else:
        plt.show() 