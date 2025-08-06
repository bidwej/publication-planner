"""Main scheduler implementation with configurable behavior options."""

from __future__ import annotations
from typing import Dict, List, Set
from datetime import date, timedelta
import random
from src.core.models import Config, Submission, Conference, SubmissionType
from src.core.dates import is_working_day


class BaseScheduler:
    """Main scheduler with configurable behavior options."""
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
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
        # Initialize
        schedule = {}
        active = set()
        current = date.today()
        backtracks = 0
        
        # Get submissions in dependency order
        ready = self._topological_order()
        
        while ready and backtracks < self.max_backtracks:
            # Sort ready submissions by priority
            ready = self._sort_by_priority(ready)
            
            # Try to schedule the first ready submission
            sid = ready[0]
            sub = self.submissions[sid]
            
            # Find earliest valid start date
            start_date = self._find_earliest_start(sub, schedule, current)
            
            if start_date and self._can_schedule(sid, start_date, schedule, active):
                # Schedule the submission
                schedule[sid] = start_date
                active.add(sid)
                ready.pop(0)
                
                # Update active set
                self._update_active_set(schedule, active, start_date)
                
            else:
                # Try backtracking if enabled
                if self.enable_backtracking and self._backtrack(schedule, active, current):
                    backtracks += 1
                    # Rebuild ready list
                    ready = self._topological_order()
                    ready = [r for r in ready if r not in schedule]
                else:
                    # Remove from ready list if we can't schedule it
                    ready.pop(0)
        
        # Print summary
        if len(schedule) != len(self.submissions):
            missing = [sid for sid in self.submissions if sid not in schedule]
            print(f"Note: Could not schedule {len(missing)} submissions: {missing}")
            print(f"Successfully scheduled {len(schedule)} out of {len(self.submissions)} submissions")
        
        return schedule
    
    def _sort_by_priority(self, ready: List[str]) -> List[str]:
        """Sort ready submissions by priority with optional randomness."""
        if not ready:
            return ready
        
        # Calculate base priorities
        priorities = []
        for sid in ready:
            sub = self.submissions[sid]
            base_priority = 0
            
            # Higher priority for submissions with deadlines
            if sub.conference_id and sub.conference_id in self.conferences:
                conf = self.conferences[sub.conference_id]
                if sub.kind in conf.deadlines and conf.deadlines[sub.kind] is not None:
                    base_priority += 100
            
            # Higher priority for papers over abstracts
            if sub.kind == SubmissionType.PAPER:
                base_priority += 50
            
            # Add randomness if enabled
            if self.randomness_factor > 0:
                random_factor = random.uniform(-self.randomness_factor, self.randomness_factor)
                base_priority += random_factor
            
            priorities.append((base_priority, sid))
        
        # Sort by priority (descending)
        priorities.sort(reverse=True)
        return [sid for _, sid in priorities]
    
    def _find_earliest_start(self, sub: Submission, schedule: Dict[str, date], current: date) -> date:
        """Find the earliest valid start date for a submission."""
        start = max(current, sub.earliest_start_date or current)
        
        # Look ahead if enabled
        if self.lookahead_days > 0:
            start += timedelta(days=self.lookahead_days)
        
        return start
    
    def _can_schedule(self, sid: str, start: date, schedule: Dict[str, date], active: Set[str]) -> bool:
        """Check if a submission can be scheduled at the given start date."""
        sub = self.submissions[sid]
        
        # Check dependencies
        if not self._deps_satisfied(sub, schedule, start):
            return False
        
        # Check deadline
        if not self._meets_deadline(sub, start):
            return False
        
        # Check concurrency limit
        if len(active) >= self.config.max_concurrent_submissions:
            return False
        
        return True
    
    def _update_active_set(self, schedule: Dict[str, date], active: Set[str], current: date):
        """Update the active set based on current date."""
        to_remove = set()
        for sid in active:
            sub = self.submissions[sid]
            end_date = self._get_end_date(schedule[sid], sub)
            if end_date < current:
                to_remove.add(sid)
        
        active -= to_remove
    
    def _backtrack(self, schedule: Dict[str, date], active: Set[str], current: date) -> bool:
        """Try to backtrack by rescheduling an active submission earlier."""
        for sid in list(active):
            if self._can_reschedule_earlier(sid, schedule, current):
                # Remove from active and schedule
                active.remove(sid)
                del schedule[sid]
                return True
        return False
    
    def _can_reschedule_earlier(self, sid: str, schedule: Dict[str, date], current: date) -> bool:
        """Check if a submission can be rescheduled earlier."""
        sub = self.submissions[sid]
        current_start = schedule[sid]
        
        # Try to find an earlier valid start date
        for days_back in range(1, 30):  # Look back up to 30 days
            new_start = current_start - timedelta(days=days_back)
            if new_start < (sub.earliest_start_date or current):
                break
            
            if self._can_schedule(sid, new_start, schedule, set()):
                schedule[sid] = new_start
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
    
    def _meets_deadline(self, sub: Submission, start: date) -> bool:
        """Check if starting on this date meets the deadline."""
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
        return end_date <= deadline
    
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