"""Penalty scoring functions."""

from typing import Dict, Any
from datetime import date, timedelta
from collections import defaultdict

from src.core.models import Config, ScheduleMetrics, SubmissionType, ConferenceType, Schedule
from src.core.constants import (
    PENALTY_CONSTANTS, REPORT_CONSTANTS
)
from src.validation.schedule import validate_schedule_constraints
# Note: Penalty costs moved to config.json because they are project-specific
# and should be configurable by users. Only algorithm constants remain in constants.py.

def calculate_penalty_score(schedule: Schedule, config: Config) -> ScheduleMetrics:
    """Calculate penalty score for a schedule based on various constraint violations.
    
    Returns:
        ScheduleMetrics with total and categorized penalty amounts
    """
    if not schedule:
        return ScheduleMetrics(
            makespan=0,
            avg_utilization=0.0,
            peak_utilization=0,
            total_penalty=0.0,
            compliance_rate=0.0,
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
    
    # Get comprehensive validation results
    comprehensive_result = validate_schedule_constraints(schedule, config)
    
    # Calculate basic penalties
    deadline_penalties = _calculate_deadline_penalties(schedule, config)
    dependency_penalties = _calculate_dependency_penalties(schedule, config)
    resource_penalties = _calculate_resource_penalties(schedule, config)
    
    # Calculate additional penalties from comprehensive validation
    # Note: These functions expect ValidationResult.metadata, not the raw result
    conference_compatibility_penalties = _calculate_conference_compatibility_penalties(comprehensive_result.metadata, config)
    abstract_paper_dependency_penalties = _calculate_abstract_paper_dependency_penalties(comprehensive_result.metadata, config)
    
    # Calculate additional penalties from README claims
    blackout_penalties = _calculate_blackout_penalties(comprehensive_result.metadata, config)
    soft_block_penalties = _calculate_soft_block_penalties(comprehensive_result.metadata, config)
    single_conference_penalties = _calculate_single_conference_penalties(comprehensive_result.metadata, config)
    lead_time_penalties = _calculate_lead_time_penalties(comprehensive_result.metadata, config)
    
    # Calculate slack cost penalties (opportunity costs)
    slack_cost_penalties = _calculate_slack_cost_penalties(schedule, config)
    
    # Sum all penalties
    total_penalty = (
        deadline_penalties +
        dependency_penalties +
        resource_penalties +
        conference_compatibility_penalties +
        abstract_paper_dependency_penalties +
        blackout_penalties +
        soft_block_penalties +
        single_conference_penalties +
        lead_time_penalties +
        slack_cost_penalties
    )
    
    return ScheduleMetrics(
        makespan=schedule.calculate_duration_days(),
        avg_utilization=0.0, # Placeholder, will be implemented
        peak_utilization=0, # Placeholder, will be implemented
        total_penalty=total_penalty,
        compliance_rate=0.0, # Placeholder, will be implemented
        quality_score=0.0, # Placeholder, will be implemented
        
        # Penalty breakdown
        deadline_penalties=deadline_penalties,
        dependency_penalties=dependency_penalties,
        resource_penalties=resource_penalties,
        conference_compatibility_penalties=conference_compatibility_penalties,
        abstract_paper_dependency_penalties=abstract_paper_dependency_penalties,
        blackout_penalties=blackout_penalties,
        soft_block_penalties=soft_block_penalties,
        single_conference_penalties=single_conference_penalties,
        lead_time_penalties=lead_time_penalties,
        slack_cost_penalties=slack_cost_penalties,
        
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

def _calculate_deadline_penalties(schedule: Schedule, config: Config) -> float:
    """Calculate penalties for missed deadlines."""
    total_penalty = 0.0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        if not sub.conference_id or not config.has_conference(sub.conference_id):
            continue
        
        conf = config.get_conference(sub.conference_id)
        if not conf or sub.kind not in conf.deadlines:
            continue
        
        deadline = conf.deadlines[sub.kind]
        
        # Calculate end date
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        end_date = interval.start_date + timedelta(days=duration)
        
        # Calculate penalty if deadline is missed
        if end_date > deadline:
            days_late = (end_date - deadline).days
            # Use config penalty costs (project-specific) instead of constants
            penalty_per_day = sub.penalty_cost_per_day or (config.penalty_costs or {}).get("default_mod_penalty_per_day", 1000.0)
            total_penalty += days_late * penalty_per_day
    
    return total_penalty

def _calculate_dependency_penalties(schedule: Schedule, config: Config) -> float:
    """Calculate penalties for dependency violations."""
    total_penalty = 0.0
    
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        for dep_id in (sub.depends_on or []):
            if dep_id not in schedule.intervals:
                # Missing dependency - use config penalty (project-specific)
                monthly_penalty = (config.penalty_costs or {}).get("default_monthly_slip_penalty", 1000.0)
                total_penalty += monthly_penalty
                continue
            
            dep_start = schedule.intervals[dep_id].start_date
            dep_sub = config.get_submission(dep_id)
            if not dep_sub:
                continue
            
            # Calculate dependency end date
            if dep_sub.kind == SubmissionType.PAPER:
                dep_duration = config.min_paper_lead_time_days
            else:
                dep_duration = 0
            
            dep_end = dep_start + timedelta(days=dep_duration)
            
            # Check if dependency is satisfied
            if interval.start_date < dep_end:
                # Dependency violation - use config penalty (project-specific)
                penalty = (config.penalty_costs or {}).get("default_dependency_violation_penalty", PENALTY_CONSTANTS.default_dependency_violation_penalty)
                total_penalty += penalty
    
    return total_penalty

def _calculate_resource_penalties(schedule: Schedule, config: Config) -> float:
    """Calculate penalties for resource constraint violations."""
    total_penalty = 0.0
    
    # Calculate daily load
    daily_load = defaultdict(int)
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        # Calculate duration
        if sub.kind == SubmissionType.PAPER:
            duration = config.min_paper_lead_time_days
        else:
            duration = 0
        
        # Add load for each day
        for i in range(duration):
            check_date = interval.start_date + timedelta(days=i)
            daily_load[check_date] += 1
    
    # Check against max concurrent submissions
    max_concurrent = config.max_concurrent_submissions
    for load in daily_load.values():
        if load > max_concurrent:
            excess = load - max_concurrent
            # Use config penalty costs (project-specific) instead of constants
            penalty_per_excess = (config.penalty_costs or {}).get("resource_violation_penalty", 200.0)
            total_penalty += excess * penalty_per_excess
    
    return total_penalty

def _calculate_blackout_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for blackout date violations."""
    blackout_result = comprehensive_result.get("blackout_dates", {})
    if not isinstance(blackout_result, dict):
        return 0.0
    
    violations = blackout_result.get("violations", [])
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("blackout_violation_penalty", 100.0)
    
    total_penalty = len(violations) * penalty_per_violation
    
    # Add additional penalties for each violation based on severity
    for violation in violations:
        severity = violation.get("severity", "medium")
        if severity == "high":
            total_penalty += penalty_per_violation * 2
        elif severity == "low":
            total_penalty += penalty_per_violation * 0.5
    
    return total_penalty


def _calculate_soft_block_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for soft block model violations (now part of resources)."""
    resource_result = comprehensive_result.get("resources", {})
    if not isinstance(resource_result, dict):
        return 0.0
    
    # Look for timing violations in the resource validation
    violations = resource_result.get("violations", [])
    timing_violations = [v for v in violations if "days_violation" in v]
    
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("soft_block_violation_penalty", 200.0)
    total_penalty = sum(v.get("days_violation", 0) * penalty_per_violation for v in timing_violations)
    
    return total_penalty


def _calculate_single_conference_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for single conference policy violations."""
    single_conf_result = comprehensive_result.get("single_conference_policy", {})
    if not isinstance(single_conf_result, dict):
        return 0.0
    
    violations = single_conf_result.get("violations", [])
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("single_conference_violation_penalty", 500.0)
    
    total_penalty = len(violations) * penalty_per_violation
    
    # Add penalties based on conference prestige
    for violation in violations:
        conference_id = violation.get("conference_id", "")
        if "ICML" in conference_id or "NeurIPS" in conference_id or "CVPR" in conference_id:
            total_penalty += penalty_per_violation * 1.5  # Higher penalty for top-tier conferences
    
    return total_penalty


def _calculate_lead_time_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for paper lead time violations."""
    lead_time_result = comprehensive_result.get("paper_lead_time", {})
    if not isinstance(lead_time_result, dict):
        return 0.0
    
    violations = lead_time_result.get("violations", [])
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("lead_time_violation_penalty", 150.0)
    
    total_penalty = len(violations) * penalty_per_violation
    
    # Add penalties based on lead time shortage
    for violation in violations:
        days_shortage = violation.get("days_shortage", 0)
        if days_shortage > 0:
            total_penalty += days_shortage * penalty_per_violation * 0.2
    
    return total_penalty


def _calculate_conference_compatibility_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for conference compatibility violations."""
    conf_compat_result = comprehensive_result.get("conference_compatibility", {})
    if not isinstance(conf_compat_result, dict):
        return 0.0
    
    violations = conf_compat_result.get("violations", [])
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("conference_compatibility_penalty", 300.0)
    
    total_penalty = len(violations) * penalty_per_violation
    
    # Add penalties based on compatibility issues
    for violation in violations:
        issue_type = violation.get("issue", "general")
        if issue_type == "submission_type_mismatch":
            total_penalty += penalty_per_violation * 1.5
        elif issue_type == "deadline_mismatch":
            total_penalty += penalty_per_violation * 1.2
    
    return total_penalty


def _calculate_abstract_paper_dependency_penalties(comprehensive_result: Dict[str, Any], config: Config) -> float:
    """Calculate penalties for abstract-paper dependency violations."""
    abstract_paper_result = comprehensive_result.get("abstract_paper_dependencies", {})
    if not isinstance(abstract_paper_result, dict):
        return 0.0
    
    violations = abstract_paper_result.get("violations", [])
    penalty_costs = config.penalty_costs or {}
    penalty_per_violation = penalty_costs.get("abstract_paper_dependency_penalty", 400.0)
    
    total_penalty = len(violations) * penalty_per_violation
    
    # Add penalties based on dependency issues
    for violation in violations:
        issue_type = violation.get("issue", "missing_dependency")
        if issue_type == "missing_dependency":
            total_penalty += penalty_per_violation * 2.0  # High penalty for missing dependencies
        elif issue_type == "timing_violation":
            total_penalty += penalty_per_violation * 1.5  # Medium penalty for timing issues
    
    return total_penalty


def _calculate_slack_cost_penalties(schedule: Schedule, config: Config) -> float:
    """Calculate penalties for slack costs (opportunity costs)."""
    total_penalty = 0.0
    
    # Calculate P_j (monthly slip penalty)
    P_j = (config.penalty_costs or {}).get("default_monthly_slip_penalty", 1000.0)
    
    # Calculate Y_j (full-year deferral penalty)
    Y_j = (config.penalty_costs or {}).get("default_full_year_deferral_penalty", 5000.0)
    
    # Calculate different missed opportunity penalties
    A_j = (config.penalty_costs or {}).get("missed_abstract_penalty", 3000.0)  # Missed abstract-only opportunity
    P_missed = (config.penalty_costs or {}).get("missed_poster_penalty", 2000.0)  # Missed poster opportunity
    AP_missed = (config.penalty_costs or {}).get("missed_abstract_paper_penalty", 4000.0)  # Missed abstract+paper opportunity
    
    # Calculate slack cost components for each submission
    for sid, interval in schedule.intervals.items():
        sub = config.get_submission(sid)
        if not sub:
            continue
        
        if sub.earliest_start_date:
            # P_j(S_j - S_j,earliest) - monthly slip penalty
            months_delay = max(0, (interval.start_date.year - sub.earliest_start_date.year) * 12 + 
                             (interval.start_date.month - sub.earliest_start_date.month))
            slip_penalty = P_j * months_delay
            
            # Y_j(1_year-deferred) - full-year deferral penalty
            if months_delay >= 12:
                deferral_penalty = Y_j
            else:
                deferral_penalty = 0
            
            # Calculate missed opportunity penalties based on submission type and conference requirements
            missed_opportunity_penalty = 0
            
            if sub.conference_id and config.has_conference(sub.conference_id):
                conf = config.get_conference(sub.conference_id)
                if not conf:
                    continue
                
                # Check for missed opportunities based on submission type and conference requirements
                if sub.kind == SubmissionType.PAPER:
                    if conf.requires_abstract_before_paper():
                        # Abstract+Paper conference - check if abstract opportunity was missed
                        missed_opportunity_penalty = AP_missed if months_delay >= 6 else 0
                    else:
                        # Paper-only conference - check if poster opportunity was missed
                        missed_opportunity_penalty = P_missed if months_delay >= 4 else 0
                elif sub.kind == SubmissionType.ABSTRACT:
                    # Abstract-only submission - check if poster opportunity was missed
                    missed_opportunity_penalty = P_missed if months_delay >= 3 else 0
                elif sub.kind == SubmissionType.POSTER:
                    # Poster submission - no additional missed opportunity penalty
                    missed_opportunity_penalty = 0
            else:
                # Generic penalty for submissions without conference assignment
                if sub.kind == SubmissionType.PAPER:
                    missed_opportunity_penalty = A_j if months_delay >= 6 else 0
                elif sub.kind == SubmissionType.ABSTRACT:
                    missed_opportunity_penalty = P_missed if months_delay >= 3 else 0
                else:  # POSTER
                    missed_opportunity_penalty = 0
            
            total_penalty += slip_penalty + deferral_penalty + missed_opportunity_penalty
    
    return total_penalty

 
