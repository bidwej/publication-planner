"""Analytics and reporting functions."""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
from datetime import date
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass

from core.models import Config, ResourceAnalysis, ScheduleAnalysis, ScheduleDistribution, SubmissionTypeAnalysis, TimelineAnalysis
from validation.resources import _calculate_daily_load
from core.constants import ANALYTICS_CONSTANTS, QUALITY_CONSTANTS


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


def analyze_schedule_completeness(schedule: Dict[str, date], config: Config) -> ScheduleAnalysis:
    """Analyze how complete the schedule is."""
    if not schedule:
        return ScheduleAnalysis(
            scheduled_count=0,
            total_count=0,
            completion_rate=0.0,
            missing_submissions=[],
            summary="No submissions to analyze"
        )
    
    total_submissions = len(config.submissions)
    scheduled_count = len(schedule)
    completion_rate = (scheduled_count / total_submissions * QUALITY_CONSTANTS.percentage_multiplier) if total_submissions > 0 else ANALYTICS_CONSTANTS.default_completion_rate
    
    # Find missing submissions
    scheduled_ids = set(schedule.keys())
    all_ids = {sub.id for sub in config.submissions}
    missing_ids = all_ids - scheduled_ids
    
    missing_submissions = [
        {
            "id": sub.id,
            "title": sub.title,
            "kind": sub.kind.value,
            "conference_id": sub.conference_id
        }
        for sub in config.submissions
        if sub.id in missing_ids
    ]
    
    return ScheduleAnalysis(
        scheduled_count=scheduled_count,
        total_count=total_submissions,
        completion_rate=completion_rate,
        missing_submissions=missing_submissions,
        summary=f"Scheduled {scheduled_count}/{total_submissions} submissions ({completion_rate:.1f}% complete)"
    )

def analyze_schedule_distribution(schedule: Dict[str, date], config: Config) -> ScheduleDistribution:
    """Analyze the distribution of submissions across time."""
    if not schedule:
        return ScheduleDistribution(
            monthly_distribution={},
            quarterly_distribution={},
            yearly_distribution={},
            summary="No submissions to analyze"
        )
    
    # Monthly distribution
    monthly_dist = {}
    for sid, start_date in schedule.items():
        month_key = f"{start_date.year}-{start_date.month:02d}"
        monthly_dist[month_key] = monthly_dist.get(month_key, 0) + 1
    
    # Quarterly distribution
    quarterly_dist = {}
    for sid, start_date in schedule.items():
        quarter = (start_date.month - 1) // 3 + 1
        quarter_key = f"{start_date.year}-Q{quarter}"
        quarterly_dist[quarter_key] = quarterly_dist.get(quarter_key, 0) + 1
    
    # Yearly distribution
    yearly_dist = {}
    for sid, start_date in schedule.items():
        year_key = str(start_date.year)
        yearly_dist[year_key] = yearly_dist.get(year_key, 0) + 1
    
    return ScheduleDistribution(
        monthly_distribution=monthly_dist,
        quarterly_distribution=quarterly_dist,
        yearly_distribution=yearly_dist,
        summary=f"Distribution across {len(monthly_dist)} months, {len(quarterly_dist)} quarters, {len(yearly_dist)} years"
    )

def analyze_submission_types(schedule: Dict[str, date], config: Config) -> SubmissionTypeAnalysis:
    """Analyze the distribution of submission types in the schedule."""
    if not schedule:
        return SubmissionTypeAnalysis(
            type_counts={},
            type_percentages={},
            summary="No submissions to analyze"
        )
    
    type_counts = {}
    sub_map = {s.id: s for s in config.submissions}
    
    for sid, start_date in schedule.items():
        sub = sub_map.get(sid)
        if not sub:
            continue
        
        sub_type = sub.kind.value
        type_counts[sub_type] = type_counts.get(sub_type, 0) + 1
    
    # Calculate percentages
    total = sum(type_counts.values())
    type_percentages = {
        sub_type: (count / total * QUALITY_CONSTANTS.percentage_multiplier) if total > 0 else ANALYTICS_CONSTANTS.default_completion_rate
        for sub_type, count in type_counts.items()
    }
    
    return SubmissionTypeAnalysis(
        type_counts=type_counts,
        type_percentages=type_percentages,
        summary=f"Distribution across {len(type_counts)} submission types"
    )

def analyze_timeline(schedule: Dict[str, date], config: Config) -> TimelineAnalysis:
    """Analyze timeline characteristics of the schedule."""
    if not schedule:
        return TimelineAnalysis(
            start_date=None,
            end_date=None,
            duration_days=0,
            avg_submissions_per_month=0.0,
            summary="No submissions to analyze"
        )
    
    # Calculate timeline metrics
    timeline_start = min(schedule.values())
    timeline_end = max(schedule.values())
    duration_days = (timeline_end - timeline_start).days + 1
    
    # Calculate daily load using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    
    # Calculate average daily load
    avg_daily_load = statistics.mean(daily_load.values()) if daily_load else 0.0
    peak_daily_load = max(daily_load.values()) if daily_load else 0
    
    return TimelineAnalysis(
        start_date=timeline_start,
        end_date=timeline_end,
        duration_days=duration_days,
        avg_submissions_per_month=avg_daily_load * ANALYTICS_CONSTANTS.monthly_conversion_factor,  # Convert daily to monthly
        summary=f"Timeline spans {duration_days} days with peak load of {peak_daily_load} submissions"
    )

def analyze_resources(schedule: Dict[str, date], config: Config) -> ResourceAnalysis:
    """Analyze resource utilization patterns."""
    if not schedule:
        return ResourceAnalysis(
            peak_load=0,
            avg_load=0.0,
            utilization_pattern={},
            summary="No submissions to analyze"
        )
    
    # Calculate daily utilization using constraints logic
    daily_load = _calculate_daily_load(schedule, config)
    
    if not daily_load:
        return ResourceAnalysis(
            peak_load=0,
            avg_load=0.0,
            utilization_pattern={},
            summary="No active days in schedule"
        )
    
    # Calculate average load
    avg_load = statistics.mean(daily_load.values())
    peak_load = max(daily_load.values())
    
    return ResourceAnalysis(
        peak_load=peak_load,
        avg_load=avg_load,
        utilization_pattern=daily_load,
        summary=f"Peak load: {peak_load}, Avg: {avg_load:.1f}"
    )


# Dependency Graph Analysis Functions

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


def analyze_dependency_graph(config: Config) -> GraphAnalysis:
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


def get_dependency_chain(submission_id: str, config: Config) -> List[str]:
    """Get the complete dependency chain for a submission."""
    nodes = _build_dependency_graph(config)
    chain = []
    visited = set()
    
    def dfs(node_id: str) -> None:
        if node_id in visited:
            return
        
        visited.add(node_id)
        node = nodes.get(node_id)
        if node:
            # Add dependencies first
            for dep_id in node.dependencies:
                dfs(dep_id)
            chain.append(node_id)
    
    dfs(submission_id)
    return chain


def get_affected_submissions(submission_id: str, config: Config) -> List[str]:
    """Get all submissions that would be affected if a submission is delayed."""
    nodes = _build_dependency_graph(config)
    affected = []
    visited = set()
    
    def dfs(node_id: str) -> None:
        if node_id in visited:
            return
        
        visited.add(node_id)
        affected.append(node_id)
        
        node = nodes.get(node_id)
        if node:
            for dependent_id in node.dependents:
                dfs(dependent_id)
    
    dfs(submission_id)
    return affected 
