from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional, Set
from dateutil.relativedelta import relativedelta
from .base import BaseScheduler
from core.types import Config, Submission, SubmissionType, SchedulerStrategy
from core.dates import is_working_day

@BaseScheduler.register_strategy(SchedulerStrategy.GREEDY)
class GreedyScheduler(BaseScheduler):
    """Greedy daily scheduler for abstracts & papers with priority weighting and blackout date handling."""
    
    def schedule(self) -> Dict[str, date]:
        """
        Greedy daily scheduler for abstracts & papers with priority weighting
        and blackout date handling.
        
        Returns
        -------
        dict
            {submission_id: start_date}
        """
        try:
            # Handle empty submissions
            if not self.submissions:
                return {}
            
            self._auto_link_abstract_paper()
            self._validate_venue_compatibility()
            topo = self._topological_order()
            
            # Global time window
            dates = [s.earliest_start_date for s in self.submissions.values()]
            for c in self.conferences.values():
                dates.extend(c.deadlines.values())
            
            if not dates:
                raise RuntimeError("No valid dates found for scheduling")
                
            current = min(dates)
            end = max(dates) + timedelta(days=self.config.min_paper_lead_time_days * 2)
            
            schedule: Dict[str, date] = {}
            active: Set[str] = set()
            
            # Early abstract scheduling if enabled
            if (self.config.scheduling_options and 
                self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
                abstract_advance = self.config.scheduling_options.get("abstract_advance_days", 30)
                self._schedule_early_abstracts(schedule, abstract_advance)
            
            max_iterations = 1000  # Prevent infinite loops
            iteration_count = 0
            
            while current <= end + timedelta(days=365) and len(schedule) < len(self.submissions):
                iteration_count += 1
                if iteration_count > max_iterations:
                    raise RuntimeError(f"Maximum iterations exceeded. Scheduled {len(schedule)}/{len(self.submissions)} submissions")
                
                # Skip blackout dates
                if not is_working_day(current, self.config.blackout_dates):
                    current += timedelta(days=1)
                    continue
                
                # Retire finished drafts
                active = {
                    sid for sid in active
                    if self._get_end_date(schedule[sid], self.submissions[sid]) > current
                }
                
                # Gather ready submissions
                ready: List[str] = []
                for sid in topo:
                    if sid in schedule:
                        continue
                    s = self.submissions[sid]
                    if not self._deps_satisfied(s, schedule, current):
                        continue
                    if current < s.earliest_start_date:
                        continue
                    ready.append(sid)
                
                # Sort by priority weight
                ready = self._sort_by_priority(ready)
                
                # Schedule up to concurrency limit
                for sid in ready:
                    if len(active) >= self.config.max_concurrent_submissions:
                        break
                    if not self._meets_deadline(self.submissions[sid], current):
                        continue
                    schedule[sid] = current
                    active.add(sid)
                
                current += timedelta(days=1)
            
            if len(schedule) != len(self.submissions):
                missing = [sid for sid in self.submissions if sid not in schedule]
                raise RuntimeError(f"Could not schedule submissions: {missing}")
            
            return schedule
            
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error in greedy scheduler: {e}")
    

    
    def _get_end_date(self, start_date: date, sub: Submission) -> date:
        """Get the end date for a submission."""
        if sub.kind == SubmissionType.ABSTRACT:
            return start_date
        else:
            # Use draft_window_months if available, otherwise fall back to config
            if sub.draft_window_months > 0:
                # Approximate months as 30 days each
                duration_days = sub.draft_window_months * 30
            else:
                duration_days = self.config.min_paper_lead_time_days
            return start_date + timedelta(days=duration_days)
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight."""
        def get_priority(sid: str) -> float:
            s = self.submissions[sid]
            weights = self.config.priority_weights or {}
            if s.kind == SubmissionType.PAPER:
                return weights.get("engineering_paper" if s.engineering else "medical_paper", 1.0)
            elif s.kind == SubmissionType.ABSTRACT:
                return weights.get("abstract", 0.5)
            else:
                return weights.get("mod", 1.5)
        
        return sorted(ready, key=get_priority, reverse=True)
    
    def _schedule_early_abstracts(self, schedule: Dict[str, date], advance_days: int) -> None:
        """Schedule abstracts early if enabled."""
        for sid, sub in self.submissions.items():
            if sub.kind != SubmissionType.ABSTRACT:
                continue
            if sub.conference_id and sub.conference_id in self.conferences:
                conf = self.conferences[sub.conference_id]
                if SubmissionType.ABSTRACT in conf.deadlines:
                    deadline = conf.deadlines[SubmissionType.ABSTRACT]
                    early_start = deadline - timedelta(days=advance_days)
                    if early_start >= sub.earliest_start_date:
                        schedule[sid] = early_start
    
    def _auto_link_abstract_paper(self) -> None:
        """Automatically link abstracts to papers if they share the same conference."""
        for sub in self.submissions.values():
            if sub.kind == SubmissionType.PAPER and sub.conference_id:
                # Find corresponding abstract
                for abs_sub in self.submissions.values():
                    if (abs_sub.kind == SubmissionType.ABSTRACT and 
                        abs_sub.conference_id == sub.conference_id):
                        if sub.id not in abs_sub.depends_on:
                            abs_sub.depends_on.append(sub.id)
    
    def _deps_satisfied(self, sub: Submission, schedule: Dict[str, date], now: date) -> bool:
        """Check if all dependencies are satisfied."""
        for dep_id in sub.depends_on:
            if dep_id not in schedule:
                return False
            dep_sub = self.submissions[dep_id]
            dep_end = self._get_end_date(schedule[dep_id], dep_sub)
            
            # For paper dependencies, add lead time
            if dep_sub.kind == SubmissionType.PAPER and sub.lead_time_from_parents > 0:
                # Add lead time in months (approximate as 30 days per month)
                lead_days = sub.lead_time_from_parents * 30
                dep_end += timedelta(days=lead_days)
            
            if dep_end > now:
                return False
        return True
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline."""
        if not sub.conference_id or sub.conference_id not in self.conferences:
            return True
        
        conf = self.conferences[sub.conference_id]
        if sub.kind not in conf.deadlines:
            return True
        
        deadline = conf.deadlines[sub.kind]
        end_date = self._get_end_date(start, sub)
        return end_date <= deadline
    
    def _topological_order(self) -> List[str]:
        """Generate topological order of submissions."""
        # Simple topological sort
        in_degree = {sid: len(self.submissions[sid].depends_on) for sid in self.submissions}
        queue = [sid for sid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for sid in self.submissions:
                if current in self.submissions[sid].depends_on:
                    in_degree[sid] -= 1
                    if in_degree[sid] == 0:
                        queue.append(sid)
        
        return result
    
    def _validate_venue_compatibility(self) -> None:
        """Validate that submissions are compatible with their venues."""
        for sub in self.submissions.values():
            if sub.conference_id and sub.conference_id not in self.conferences:
                raise ValueError(f"Submission {sub.id} references unknown conference {sub.conference_id}") 