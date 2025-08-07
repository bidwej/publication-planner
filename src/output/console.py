"""Console output formatting for schedules."""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import date, timedelta
import statistics
from core.models import Config, SchedulerStrategy
from core.constants import MAX_TITLE_LENGTH
from core.constraints import validate_schedule_comprehensive
from scoring.penalty import calculate_penalty_score
from scoring.efficiency import calculate_efficiency_score
from scoring.quality import calculate_quality_score


def print_schedule_summary(schedule: Dict[str, date], config: Config) -> None:
    """Print a summary of the schedule to console."""
    if not schedule:
        print("No schedule generated.")
        return
    
    print("\n=== Schedule Summary ===")
    print(f"Total submissions: {len(schedule)}")
    print(f"Date range: {min(schedule.values())} to {max(schedule.values())}")
    
    # Count by type
    abstracts = papers = 0
    sub_map = {s.id: s for s in config.submissions}
    for sid in schedule:
        sub = sub_map.get(sid)
        if sub:
            abstracts += sub.kind.value == "abstract"
            papers += sub.kind.value == "paper"
    
    print(f"Abstracts: {abstracts}")
    print(f"Papers: {papers}")
    print()


def print_deadline_status(schedule: Dict[str, date], config: Config) -> None:
    """Print deadline status information."""
    if not schedule:
        return
    
    print("\n=== Deadline Status ===")
    
    on_time = late = total = 0
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub or not sub.conference_id or sub.conference_id not in config.conferences_dict:
            continue
        
        conf = config.conferences_dict[sub.conference_id]
        if sub.kind not in conf.deadlines:
            continue
        
        total += 1
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        duration = config.min_paper_lead_time_days if sub.kind.value == "PAPER" else 0
        end_date = start_date + timedelta(days=duration)
        
        if end_date <= deadline:
            on_time += 1
        else:
            late += 1
            days_late = (end_date - deadline).days
            print(f"  LATE: {sid} ({sub.title[:MAX_TITLE_LENGTH]}) - {days_late} days late")
    
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
    
    print("\n=== Resource Utilization ===")
    
    # Calculate daily utilization
    daily_load = {}
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        duration = config.min_paper_lead_time_days if sub.kind.value == "PAPER" else 0
        
        # Add load for each day
        for i in range(duration + 1):
            day = start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    if not daily_load:
        return
    
    max_load = max(daily_load.values())
    avg_load = statistics.mean(daily_load.values())
    max_utilization = max_load / config.max_concurrent_submissions
    avg_utilization = avg_load / config.max_concurrent_submissions
    
    print(f"Max concurrent submissions: {max_load}")
    print(f"Average daily load: {avg_load:.1f}")
    print(f"Max utilization: {max_utilization:.1%}")
    print(f"Average utilization: {avg_utilization:.1%}")
    print()


def print_metrics_summary(schedule: Dict[str, date], config: Config) -> None:
    """Print a comprehensive metrics summary."""
    print("\n=== Metrics Summary ===")
    
    if not schedule:
        print("No schedule to analyze.")
        print()
        return
    
    from core.constraints import validate_deadline_compliance
    from scoring.quality import calculate_quality_score
    from scoring.efficiency import calculate_efficiency_score
    
    # Calculate metrics
    penalty_breakdown = calculate_penalty_score(schedule, config)
    quality_score = calculate_quality_score(schedule, config)
    efficiency_score = calculate_efficiency_score(schedule, config)
    deadline_validation = validate_deadline_compliance(schedule, config)
    
    print(f"Penalty score: ${penalty_breakdown.total_penalty:.2f}")
    print(f"Quality score: {quality_score:.3f}")
    print(f"Efficiency score: {efficiency_score:.3f}")
    print(f"Deadline compliance: {deadline_validation.compliance_rate:.1f}%")
    print()


def print_schedule_analysis(schedule: Dict[str, date], config: Config, strategy_name: str = "Unknown") -> None:
    """Print comprehensive schedule analysis."""
    if not schedule:
        print(f"No schedule generated for {strategy_name}")
        return
    
    print(f"\n{'='*60}")
    print(f"SCHEDULE ANALYSIS: {strategy_name.upper()}")
    print(f"{'='*60}")
    
    # Print basic summary
    print_schedule_summary(schedule, config)
    
    # Comprehensive validation using all constraints, scoring, and analytics
    validation_result = validate_schedule_comprehensive(schedule, config)
    
    print("Comprehensive Schedule Analysis:")
    print(f"  Feasibility: {'✓' if validation_result['overall_valid'] else '✗'}")
    print(f"  Completion: {validation_result['completion_rate']:.1f}%")
    print(f"  Duration: {validation_result['duration_days']} days")
    print(f"  Peak Load: {validation_result['peak_load']} submissions")
    print(f"  Quality Score: {validation_result['quality_score']:.1f}/100")
    print(f"  Efficiency Score: {validation_result['efficiency_score']:.1f}/100")
    print(f"  Total Penalty: ${validation_result['total_penalty']:.2f}")
    print(f"  Total Violations: {validation_result['summary']['total_violations']}")
    
    # Print detailed metrics
    print_metrics_summary(schedule, config)


def print_strategy_comparison(results: Dict[str, Dict[str, date]], config: Config, output_file: Optional[str] = None) -> None:
    """Print comparison of different scheduling strategies."""
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    comparison_data = []
    
    from scoring.quality import calculate_quality_score
    from scoring.efficiency import calculate_efficiency_score
    
    for strategy_name, schedule in results.items():
        penalty = calculate_penalty_score(schedule, config)
        quality = calculate_quality_score(schedule, config)
        efficiency = calculate_efficiency_score(schedule, config)
        
        print(f"\n{strategy_name}:")
        print(f"  Penalty: ${penalty.total_penalty:.2f}")
        print(f"  Quality: {quality:.3f}")
        print(f"  Efficiency: {efficiency:.3f}")
        print(f"  Submissions: {len(schedule)}")
        
        comparison_data.append({
            'strategy': strategy_name,
            'penalty': penalty.total_penalty,
            'quality': quality,
            'efficiency': efficiency,
            'submissions': len(schedule)
        })
    
    # Save comparison results if output file specified
    if output_file:
        try:
            import json
            with open(output_file, 'w') as f:
                json.dump(comparison_data, f, indent=2)
            print(f"\nComparison results saved to: {output_file}")
        except Exception as e:
            print(f"Error saving comparison results: {e}")


def print_available_strategies() -> None:
    """Print all available scheduling strategies."""
    print("Available scheduling strategies:")
    for strategy in SchedulerStrategy:
        print(f"  - {strategy.value}")
    print("\nUse --strategy <name> to specify a strategy.")


def format_table(data: List[Dict[str, Any]], title: str = "") -> str:
    """Format data as a table string."""
    if not data:
        return title + "\n" if title else ""
    
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
        lines.extend([title, ""])
    
    # Header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    lines.extend([header, "-" * len(header)])
    
    # Rows
    for row in data:
        row_str = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        lines.append(row_str)
    
    return "\n".join(lines) 