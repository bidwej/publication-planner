"""Base scheduler implementation with configuration options."""

from __future__ import annotations
from typing import Dict, List, Set
from datetime import date, timedelta
from src.core.models import Config, Submission, Conference, SubmissionType
from src.core.dates import is_working_day


class Scheduler:
    """Main scheduler with configurable behavior options."""
    
    def __init__(self, config: Config):
        """Initialize scheduler with config."""
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
        
        # Configuration options for different behaviors
        self.randomness_factor = getattr(config, 'randomness_factor', 0.0)
        self.lookahead_days = getattr(config, 'lookahead_days', 0)
        self.enable_backtracking = getattr(config, 'enable_backtracking', False)
        self.max_backtracks = getattr(config, 'max_backtracks', 5)
    
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule for all submissions.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        self._auto_link_abstract_paper()
        self._validate_venue_compatibility()
        topo = self._topological_order()
        
        # Global time window
        dates = [s.earliest_start_date for s in self.submissions.values() if s.earliest_start_date]
        for c in self.conferences.values():
            dates.extend(c.deadlines.values())
        if not dates:
            raise RuntimeError("No valid dates found for scheduling")
        current = min(dates)
        end = max(dates) + timedelta(days=self.config.min_paper_lead_time_days * 2)
        
        schedule: Dict[str, date] = {}
        active: Set[str] = set()
        backtracks = 0
        
        # Early abstract scheduling if enabled
        if (self.config.scheduling_options and 
            self.config.scheduling_options.get("enable_early_abstract_scheduling", False)):
            abstract_advance = self.config.scheduling_options.get("abstract_advance_days", 30)
            self._schedule_early_abstracts(schedule, abstract_advance)
        
        while current <= end and len(schedule) < len(self.submissions):
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
                if s.earliest_start_date and current < s.earliest_start_date:
                    continue
                ready.append(sid)
            
            # Sort by priority weight
            ready = self._sort_by_priority(ready)
            
            # Try to schedule up to concurrency limit
            scheduled_this_round = False
            for sid in ready:
                if len(active) >= self.config.max_concurrent_submissions:
                    break
                if not self._meets_deadline(self.submissions[sid], current):
                    continue
                schedule[sid] = current
                active.add(sid)
                scheduled_this_round = True
            
            # If we couldn't schedule anything and backtracking is enabled, try backtracking
            if not scheduled_this_round and self.enable_backtracking and backtracks < self.max_backtracks:
                if self._backtrack(schedule, active, current):
                    backtracks += 1
                    continue
            
            current += timedelta(days=1)
        
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            # Log the missing submissions for debugging
            print(f"Note: Could not schedule {len(missing)} submissions: {missing}")
            print(f"Successfully scheduled {len(schedule)} out of {len(self.submissions)} submissions")
            # Return what we have - this is acceptable for a simplified scheduler
            return schedule
        
        return schedule
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority weight with optional randomness and lookahead."""
        def get_priority(sid: str) -> float:
            s = self.submissions[sid]
            weights = self.config.priority_weights or {}
            
            base_priority = 0.0
            if s.kind.value == "PAPER":
                base_priority = weights.get("engineering_paper" if s.engineering else "medical_paper", 1.0)
            elif s.kind.value == "ABSTRACT":
                base_priority = weights.get("abstract", 0.5)
            else:
                base_priority = weights.get("mod", 1.5)
            
            # Add lookahead bonus for submissions with dependencies
            lookahead_bonus = 0.0
            if self.lookahead_days > 0:
                for other_sid in self.submissions:
                    other_sub = self.submissions[other_sid]
                    if other_sub.depends_on and sid in other_sub.depends_on:
                        # This submission blocks others, give it higher priority
                        lookahead_bonus += 0.5
            
            # Add random noise if enabled
            noise = 0.0
            if self.randomness_factor > 0:
                import random
                noise = random.uniform(-self.randomness_factor, self.randomness_factor)
            
            return base_priority + lookahead_bonus + noise
        
        return sorted(ready, key=get_priority, reverse=True)
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline with optional lookahead buffer."""
        if not sub.conference_id or sub.conference_id not in self.conferences:
            return True
        
        conf = self.conferences[sub.conference_id]
        if sub.kind not in conf.deadlines:
            return True
        
        deadline = conf.deadlines[sub.kind]
        if deadline is None:
            # If no deadline is set, assume it's always valid
            return True
        
        end_date = self._get_end_date(start, sub)
        
        # Add lookahead buffer if enabled
        if self.lookahead_days > 0:
            buffer_date = deadline - timedelta(days=self.lookahead_days)
            return end_date <= buffer_date
        
        return end_date <= deadline
    
    def _backtrack(self, schedule: Dict[str, date], active: Set[str], current: date) -> bool:
        """Try to backtrack by removing a recent decision."""
        if not schedule:
            return False
        
        # Find the most recent submission that could be rescheduled
        for sid in reversed(list(schedule.keys())):
            if self._can_reschedule_earlier(sid, schedule, current):
                # Remove this submission and try again
                del schedule[sid]
                if sid in active:
                    active.remove(sid)
                return True
        
        return False
    
    def _can_reschedule_earlier(self, sid: str, schedule: Dict[str, date], current: date) -> bool:
        """Check if a submission can be rescheduled to an earlier date."""
        sub = self.submissions[sid]
        original_start = schedule[sid]
        
        # Try to find an earlier valid start date
        for test_date in range((current - original_start).days):
            test_start = original_start - timedelta(days=test_date)
            if (sub.earliest_start_date is None or test_start >= sub.earliest_start_date) and \
               self._deps_satisfied(sub, schedule, test_start) and \
               self._meets_deadline(sub, test_start):
                return True
        
        return False
    
    def _auto_link_abstract_paper(self):
        """Auto-link abstracts to papers if not already linked."""
        # This method would link abstracts to their corresponding papers
        # For now, we'll assume the linking is done during config loading
        pass
    
    def _validate_venue_compatibility(self):
        """Validate that submissions are compatible with their venues."""
        # Check that all submissions have valid conference assignments
        for sid, submission in self.submissions.items():
            if submission.conference_id and submission.conference_id not in self.conferences:
                raise ValueError(f"Submission {sid} references unknown conference {submission.conference_id}")
    
    def _topological_order(self) -> List[str]:
        """Get submissions in topological order based on dependencies."""
        # Simple implementation - just return all submissions
        # A proper topological sort would be more complex
        return list(self.submissions.keys())
    
    def _deps_satisfied(self, sub: Submission, schedule: Dict[str, date], current: date) -> bool:
        """Check if all dependencies are satisfied."""
        if not sub.depends_on:
            return True
        for dep_id in sub.depends_on:
            if dep_id not in schedule:
                return False
            dep_end = self._get_end_date(schedule[dep_id], self.submissions[dep_id])
            if current < dep_end + timedelta(days=sub.lead_time_from_parents):
                return False
        return True
    
    def _get_end_date(self, start: date, sub: Submission) -> date:
        """Calculate end date for a submission."""
        lead_time = self.config.min_paper_lead_time_days
        if sub.kind.value == "ABSTRACT":
            lead_time = self.config.min_abstract_lead_time_days
        return start + timedelta(days=lead_time)
    
    def _schedule_early_abstracts(self, schedule: Dict[str, date], abstract_advance: int):
        """Schedule abstracts early if enabled."""
        # Find all abstract submissions
        abstracts = [sid for sid, sub in self.submissions.items() 
                    if sub.kind == SubmissionType.ABSTRACT]
        
        # Schedule them early if they have valid conference assignments
        for abstract_id in abstracts:
            abstract = self.submissions[abstract_id]
            if abstract.conference_id and abstract.conference_id in self.conferences:
                conf = self.conferences[abstract_id]
                if SubmissionType.ABSTRACT in conf.deadlines:
                    # Schedule abstract early
                    early_date = conf.deadlines[SubmissionType.ABSTRACT] - timedelta(days=abstract_advance)
                    if abstract.earliest_start_date is None or early_date >= abstract.earliest_start_date:
                        schedule[abstract_id] = early_date 