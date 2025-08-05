"""Console output formatting for schedules."""

from typing import Dict, Any, List
from datetime import date, timedelta
from ..models import Config

def print_schedule_summary(schedule: Dict[str, date], config: Config) -> None:
    """Print a summary of the schedule to console."""
    if not schedule:
        print("No schedule generated.")
        return
    
    print(f"\n=== Schedule Summary ===")
    print(f"Total submissions: {len(schedule)}")
    print(f"Date range: {min(schedule.values())} to {max(schedule.values())}")
    
    # Count by type
    abstracts = 0
    papers = 0
    for sid in schedule:
        sub = config.submissions_dict.get(sid)
        if sub:
            if sub.kind.value == "ABSTRACT":
                abstracts += 1
            else:
                papers += 1
    
    print(f"Abstracts: {abstracts}")
    print(f"Papers: {papers}")
    print()

def print_deadline_status(schedule: Dict[str, date], config: Config) -> None:
    """Print deadline status information."""
    if not schedule:
        return
    
    print(f"\n=== Deadline Status ===")
    
    on_time = 0
    late = 0
    total = 0
    
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub or not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        total += 1
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind.value == "PAPER":
            duration = config.min_paper_lead_time_days
            end_date = start_date + timedelta(days=duration)
        else:
            end_date = start_date
        
        if end_date <= deadline:
            on_time += 1
        else:
            late += 1
            days_late = (end_date - deadline).days
            print(f"  LATE: {sid} ({sub.title[:30]}...) - {days_late} days late")
    
    if total > 0:
        print(f"On time: {on_time}/{total} ({on_time/total*100:.1f}%)")
        print(f"Late: {late}/{total} ({late/total*100:.1f}%)")
    else:
        print("No submissions with deadlines found")
    print()

def print_utilization_summary(schedule: Dict[str, date], config: Config) -> None:
    """Print resource utilization summary."""
    if not schedule:
        return
    
    print(f"\n=== Resource Utilization ===")
    
    # Calculate daily utilization
    daily_load = {}
    for sid, start_date in schedule.items():
        sub = config.submissions_dict.get(sid)
        if not sub:
            continue
        
        if sub.kind.value == "PAPER":
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    if not daily_load:
        return
    
    max_load = max(daily_load.values())
    avg_load = sum(daily_load.values()) / len(daily_load)
    max_utilization = max_load / config.max_concurrent_submissions
    avg_utilization = avg_load / config.max_concurrent_submissions
    
    print(f"Max concurrent submissions: {max_load}")
    print(f"Average daily load: {avg_load:.1f}")
    print(f"Max utilization: {max_utilization:.1%}")
    print(f"Average utilization: {avg_utilization:.1%}")
    print()

def print_metrics_summary(schedule: Dict[str, date], config: Config) -> None:
    """Print a comprehensive metrics summary."""
    if not schedule:
        return
    
    print(f"\n=== Metrics Summary ===")
    
    # Import metrics functions
    from metrics.makespan import calculate_makespan
    from metrics.utilization import calculate_resource_utilization
    from metrics.penalties import calculate_penalty_costs
    from metrics.deadlines import calculate_deadline_compliance
    from metrics.quality import calculate_schedule_quality_score
    
    # Calculate metrics
    makespan = calculate_makespan(schedule, config)
    utilization = calculate_resource_utilization(schedule, config)
    penalties = calculate_penalty_costs(schedule, config)
    compliance = calculate_deadline_compliance(schedule, config)
    quality_score = calculate_schedule_quality_score(schedule, config)
    
    print(f"Makespan: {makespan} days")
    print(f"Average utilization: {utilization['avg_utilization']:.1%}")
    print(f"Max utilization: {utilization['max_utilization']:.1%}")
    print(f"Total penalties: ${penalties['total_penalty']:.2f}")
    print(f"Deadline compliance: {compliance['compliance_rate']:.1f}%")
    print(f"Quality score: {quality_score:.3f}")
    print()

def format_table(data: List[Dict[str, Any]], title: str = "") -> str:
    """Format data as a table string."""
    if not data:
        return ""
    
    # Get all column names
    columns = list(data[0].keys())
    
    # Calculate column widths
    widths = {}
    for col in columns:
        widths[col] = len(col)
        for row in data:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))
    
    # Build table
    lines = []
    if title:
        lines.append(title)
        lines.append("")
    
    # Header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.append(header)
    lines.append("-" * len(header))
    
    # Rows
    for row in data:
        row_str = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(row_str)
    
    return "\n".join(lines) 