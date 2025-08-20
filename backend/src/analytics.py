"""Analytics and reporting functions."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
from datetime import date, timedelta
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass

from src.core.models import Config, Schedule, ScheduleMetrics, SubmissionType
from src.validation.resources import _calculate_daily_load
from src.core.constants import ANALYTICS_CONSTANTS, QUALITY_CONSTANTS, SCHEDULING_CONSTANTS
from src.validation.deadline import validate_deadline_constraints
from src.validation.resources import validate_resources_constraints
from src.scoring.efficiency import calculate_efficiency_score
from src.scoring.penalties import calculate_penalty_score
from src.scoring.quality import calculate_quality_score


@dataclass
class GraphNode:
    """A node in the dependency graph."""
    submission_id: str
    dependencies: List[str]
    dependents: List[str]
    depth: int = 0
    critical_path: bool = False


@dataclass
class GraphAnalysis:
    """Results of dependency graph analysis."""
    nodes: Dict[str, GraphNode]
    cycles: List[List[str]]
    bottlenecks: List[str]
    critical_path: List[str]
    max_depth: int
    isolated_nodes: List[str]
    summary: str


# ============================================================================
# PUBLIC FUNCTIONS
# ============================================================================

def generate_schedule_summary(schedule: Schedule, config: Config) -> ScheduleMetrics:
    """Generate comprehensive schedule analysis and metrics in one unified model."""
    if not schedule:
        return ScheduleMetrics(
            makespan=0,
            avg_utilization=0.0,
            peak_utilization=0,
            total_penalty=0.0,
            compliance_rate=100.0,
            quality_score=0.0,
            duration_days=0,
            avg_daily_load=0.0,
            timeline_efficiency=0.0,
            utilization_rate=0.0,
            efficiency_score=0.0,
            submission_count=0,
            scheduled_count=0,
            completion_rate=0.0,
            monthly_distribution={},
            quarterly_distribution={},
            yearly_distribution={},
            type_counts={},
            type_percentages={},
            missing_submissions=[],
            start_date=None,
            end_date=None
        )
    
    # Basic schedule metrics using intervals
    start_date = min(interval.start_date for interval in schedule.intervals.values())
    end_date = max(interval.end_date for interval in schedule.intervals.values())
    schedule_span = schedule.calculate_duration_days()
    duration_days = (end_date - start_date).days if start_date and end_date else 0
    
    # Calculate scores
    penalty = calculate_penalty_score(schedule, config)
    quality = calculate_quality_score(schedule, config)
    efficiency = calculate_efficiency_score(schedule, config)
    
    # Calculate compliance
    deadline_validation = validate_deadline_constraints(schedule, config)
    resource_validation = validate_resources_constraints(schedule, config)
    
    # Calculate daily load for utilization metrics
    daily_load = {}
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)  # Use new type-safe method
        if not sub:
            continue
        
        duration = sub.get_duration_days(config)
        for i in range(duration):
            day = interval.start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    # Calculate utilization metrics
    avg_utilization = statistics.mean(daily_load.values()) if daily_load else 0.0
    peak_utilization = max(daily_load.values()) if daily_load else 0
    avg_daily_load = avg_utilization
    utilization_rate = min((avg_utilization / config.max_concurrent_submissions) * 100, 100.0) if config.max_concurrent_submissions > 0 else 0.0
    
    # Calculate timeline efficiency
    timeline_efficiency = min((duration_days / max(schedule_span, 1)) * 100, 100.0) if schedule_span > 0 else 0.0
    
    # Calculate submission counts and completion
    total_submissions = len(config.submissions)
    scheduled_count = len(schedule.intervals)
    completion_rate = min((scheduled_count / total_submissions * 100), 100.0) if total_submissions > 0 else 0.0
    
    # Calculate type distribution (only for scheduled submissions)
    type_counts = {}
    type_percentages = {}
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if sub:
            sub_type = sub.kind.value
            type_counts[sub_type] = type_counts.get(sub_type, 0) + 1
    
    for sub_type, count in type_counts.items():
        type_percentages[sub_type] = (count / scheduled_count * 100) if scheduled_count > 0 else 0.0
    
    # Calculate time distribution (count ongoing submissions, not just start dates)
    monthly_dist = {}
    quarterly_dist = {}
    yearly_dist = {}
    
    for sid, interval in schedule.intervals.items():
        start_date = interval.start_date
        end_date = interval.end_date
        
        # Count submissions for each month they span
        current_date = start_date
        while current_date <= end_date:
            month_key = f"{current_date.year}-{current_date.month:02d}"
            monthly_dist[month_key] = monthly_dist.get(month_key, 0) + 1
            
            quarter = (current_date.month - 1) // 3 + 1
            quarter_key = f"{current_date.year}-Q{quarter}"
            quarterly_dist[quarter_key] = quarterly_dist.get(quarter_key, 0) + 1
            
            year_key = str(current_date.year)
            yearly_dist[year_key] = yearly_dist.get(year_key, 0) + 1
            
            # Move to next month (handle day overflow properly)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                # Use the first day of the next month to avoid day overflow
                current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    # Find missing submissions
    scheduled_ids = set(schedule.intervals.keys())
    missing_submissions = [
        {
            "id": sub.id,
            "title": sub.title,
            "kind": sub.kind.value,
            "conference_id": sub.conference_id
        }
        for sub in config.submissions
        if sub.id not in scheduled_ids
    ]
    
    return ScheduleMetrics(
        makespan=schedule_span,
        total_penalty=penalty.total_penalty,
        compliance_rate=deadline_validation.metadata.get("compliance_rate", 100.0),
        quality_score=quality,
        avg_utilization=avg_utilization,
        peak_utilization=peak_utilization,
        utilization_rate=utilization_rate,
        efficiency_score=efficiency,
        duration_days=duration_days,
        avg_daily_load=avg_daily_load,
        timeline_efficiency=timeline_efficiency,
        submission_count=total_submissions,
        scheduled_count=scheduled_count,
        completion_rate=completion_rate,
        monthly_distribution=monthly_dist,
        quarterly_distribution=quarterly_dist,
        yearly_distribution=yearly_dist,
        type_counts=type_counts,
        type_percentages=type_percentages,
        missing_submissions=missing_submissions,
        start_date=start_date,
        end_date=end_date
    )


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================

def _analyze_dependency_graph(config: Config) -> GraphAnalysis:
    """Analyze dependency graphs for submissions."""
    nodes = _build_dependency_graph(config)
    
    # Detect cycles
    cycles = _detect_cycles(nodes)
    
    # Calculate depths
    depths = _calculate_depths(nodes)
    max_depth = max(depths.values()) if depths else 0
    
    # Find critical path
    critical_path = _find_critical_path(nodes)
    
    # Find bottlenecks
    bottlenecks = _find_bottlenecks(nodes)
    
    # Find isolated nodes
    isolated_nodes = _find_isolated_nodes(nodes)
    
    # Generate summary
    summary = f"Graph Analysis: {len(nodes)} nodes, {len(cycles)} cycles, " \
             f"max depth {max_depth}, {len(bottlenecks)} bottlenecks, " \
             f"{len(isolated_nodes)} isolated nodes"
    
    return GraphAnalysis(
        nodes=nodes,
        cycles=cycles,
        bottlenecks=bottlenecks,
        critical_path=critical_path,
        max_depth=max_depth,
        isolated_nodes=isolated_nodes,
        summary=summary
    )


def _build_dependency_graph(config: Config) -> Dict[str, GraphNode]:
    """Build the dependency graph from submissions."""
    nodes = {}
    
    # Create nodes
    for submission in config.submissions:
        nodes[submission.id] = GraphNode(
            submission_id=submission.id,
            dependencies=submission.depends_on or [],
            dependents=[],
            depth=0,
            critical_path=False
        )
    
    # Build dependency relationships
    for submission in config.submissions:
        if submission.depends_on:
            for dep_id in submission.depends_on:
                if dep_id in nodes:
                    nodes[dep_id].dependents.append(submission.id)
    
    return nodes


def _detect_cycles(nodes: Dict[str, GraphNode]) -> List[List[str]]:
    """Detect cycles in the dependency graph."""
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node_id: str, path: List[str]) -> None:
        if node_id in rec_stack:
            # Found a cycle
            cycle_start = path.index(node_id)
            cycle = path[cycle_start:] + [node_id]
            cycles.append(cycle)
            return
        
        if node_id in visited:
            return
        
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)
        
        node = nodes.get(node_id)
        if node:
            for dep_id in node.dependencies:
                dfs(dep_id, path.copy())
        
        rec_stack.remove(node_id)
    
    for node_id in nodes:
        if node_id not in visited:
            dfs(node_id, [])
    
    return cycles


def _calculate_depths(nodes: Dict[str, GraphNode]) -> Dict[str, int]:
    """Calculate the depth of each node in the dependency graph."""
    depths = {}
    in_degree = defaultdict(int)
    
    # Calculate in-degrees
    for node in nodes.values():
        for dep_id in node.dependencies:
            in_degree[dep_id] += 1
    
    # Topological sort with depth calculation
    queue = deque()
    for node_id in nodes:
        if in_degree[node_id] == 0:
            queue.append(node_id)
            depths[node_id] = 0
    
    while queue:
        node_id = queue.popleft()
        current_depth = depths[node_id]
        
        node = nodes[node_id]
        for dependent_id in node.dependents:
            in_degree[dependent_id] -= 1
            depths[dependent_id] = max(depths.get(dependent_id, 0), current_depth + 1)
            
            if in_degree[dependent_id] == 0:
                queue.append(dependent_id)
    
    # Update node depths
    for node_id, depth in depths.items():
        if node_id in nodes:
            nodes[node_id].depth = depth
    
    return depths


def _find_critical_path(nodes: Dict[str, GraphNode]) -> List[str]:
    """Find the critical path in the dependency graph."""
    depths = _calculate_depths(nodes)
    max_depth = max(depths.values()) if depths else 0
    
    # Find nodes at maximum depth
    max_depth_nodes = [node_id for node_id, depth in depths.items() if depth == max_depth]
    
    # Find the longest path to each max depth node
    critical_path = []
    max_path_length = 0
    
    for end_node in max_depth_nodes:
        path = _find_longest_path_to_node(end_node, nodes)
        if len(path) > max_path_length:
            max_path_length = len(path)
            critical_path = path
    
    # Mark critical path nodes
    for node_id in critical_path:
        if node_id in nodes:
            nodes[node_id].critical_path = True
    
    return critical_path


def _find_longest_path_to_node(target_node: str, nodes: Dict[str, GraphNode]) -> List[str]:
    """Find the longest path to a specific node."""
    def dfs(node_id: str, path: List[str], visited: Set[str]) -> List[str]:
        if node_id == target_node:
            return path + [node_id]
        
        if node_id in visited:
            return []
        
        visited.add(node_id)
        longest_path = []
        
        node = nodes.get(node_id)
        if node:
            for dep_id in node.dependencies:
                new_path = dfs(dep_id, path + [node_id], visited.copy())
                if len(new_path) > len(longest_path):
                    longest_path = new_path
        
        return longest_path
    
    # Start from nodes with no dependencies
    start_nodes = [node_id for node_id, node in nodes.items() 
                  if not node.dependencies]
    
    longest_path = []
    for start_node in start_nodes:
        path = dfs(start_node, [], set())
        if len(path) > len(longest_path):
            longest_path = path
    
    return longest_path


def _find_bottlenecks(nodes: Dict[str, GraphNode]) -> List[str]:
    """Find bottleneck nodes in the dependency graph."""
    bottlenecks = []
    
    # Calculate in-degrees and out-degrees
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    
    for node in nodes.values():
        for dep_id in node.dependencies:
            in_degree[dep_id] += 1
        out_degree[node.submission_id] = len(node.dependents)
    
    # Find nodes with high in-degree or out-degree
    for node_id, node in nodes.items():
        in_deg = in_degree[node_id]
        out_deg = out_degree[node_id]
        
        # Bottleneck criteria: high in-degree or high out-degree
        if in_deg > 2 or out_deg > 2:
            bottlenecks.append(node_id)
    
    return bottlenecks


def _find_isolated_nodes(nodes: Dict[str, GraphNode]) -> List[str]:
    """Find nodes with no dependencies or dependents."""
    isolated = []
    
    for node_id, node in nodes.items():
        if not node.dependencies and not node.dependents:
            isolated.append(node_id)
    
    return isolated


def analyze_timeline(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Analyze timeline information for the schedule."""
    if not schedule:
        return {
            "start_date": None,
            "end_date": None,
            "duration_days": 0,
            "avg_submissions_per_month": 0.0,
            "summary": "No schedule to analyze"
        }
    
    # Basic timeline metrics using intervals
    start_date = min(interval.start_date for interval in schedule.intervals.values())
    end_date = max(interval.end_date for interval in schedule.intervals.values())
    duration_days = (end_date - start_date).days if start_date and end_date else 0
    
    # Calculate average submissions per month
    months = max(1, duration_days // 30)
    avg_submissions_per_month = len(schedule.intervals) / months if months > 0 else 0.0
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "duration_days": duration_days,
        "avg_submissions_per_month": avg_submissions_per_month,
        "summary": f"Schedule spans {duration_days} days with {len(schedule.intervals)} submissions"
    }


def analyze_resources(schedule: Schedule, config: Config) -> Dict[str, Any]:
    """Analyze resource utilization for the schedule."""
    if not schedule:
        return {
            "peak_load": 0,
            "avg_load": 0.0,
            "utilization_pattern": "empty",
            "summary": "No schedule to analyze"
        }
    
    # Calculate daily load for utilization metrics
    daily_load = {}
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        duration = sub.get_duration_days(config)
        for i in range(duration):
            day = interval.start_date + timedelta(days=i)
            daily_load[day] = daily_load.get(day, 0) + 1
    
    if not daily_load:
        return {
            "peak_load": 0,
            "avg_load": 0.0,
            "utilization_pattern": "no_load",
            "summary": "No daily load calculated"
        }
    
    # Calculate utilization metrics
    avg_load = statistics.mean(daily_load.values()) if daily_load else 0.0
    peak_load = max(daily_load.values()) if daily_load else 0
    utilization_rate = min((avg_load / config.max_concurrent_submissions) * 100, 100.0) if config.max_concurrent_submissions > 0 else 0.0
    
    # Determine utilization pattern
    if peak_load <= config.max_concurrent_submissions:
        pattern = "under_utilized"
    elif peak_load <= config.max_concurrent_submissions * 1.2:
        pattern = "well_utilized"
    else:
        pattern = "over_utilized"
    
    return {
        "peak_load": peak_load,
        "avg_load": avg_load,
        "utilization_pattern": pattern,
        "summary": f"Peak load: {peak_load}, Average: {avg_load:.1f}, Pattern: {pattern}"
    }


def analyze_schedule_with_scoring(schedule, config: Config) -> ScheduleMetrics:
    """
    Analyze complete schedule with comprehensive analytics.
    
    This function now returns the unified ScheduleMetrics model.
    """
    return generate_schedule_summary(schedule, config) 
