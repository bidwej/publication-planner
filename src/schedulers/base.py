from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import date, timedelta
from core.types import Config, Submission

class BaseScheduler(ABC):
    """Abstract base class for all schedulers."""
    
    def __init__(self, config: Config):
        self.config = config
        self.submissions = {s.id: s for s in config.submissions}
        self.conferences = {c.id: c for c in config.conferences}
    
    @abstractmethod
    def schedule(self) -> Dict[str, date]:
        """
        Generate a schedule for all submissions.
        
        Returns
        -------
        Dict[str, date]
            Mapping of submission_id to start_date
        """
        pass
    
    def validate_schedule(self, schedule: Dict[str, date]) -> bool:
        """Validate that a schedule meets all constraints."""
        # Check that all submissions are scheduled
        if len(schedule) != len(self.submissions):
            return False
        
        # Check dependencies
        for sid, start_date in schedule.items():
            sub = self.submissions[sid]
            for dep_id in sub.depends_on:
                if dep_id not in schedule:
                    return False
                dep_start = schedule[dep_id]
                if start_date <= dep_start:
                    return False
        
        return True
    
    def get_schedule_metrics(self, schedule: Dict[str, date]) -> Dict[str, float]:
        """Calculate metrics for a given schedule."""
        if not schedule:
            return {}
        
        # Calculate makespan
        end_dates = []
        for sid, start_date in schedule.items():
            sub = self.submissions[sid]
            if sub.kind.value == "PAPER":
                duration = self.config.min_paper_lead_time_days
            else:
                duration = 0
            end_dates.append(start_date + timedelta(days=duration))
        
        makespan = max(end_dates) - min(schedule.values())
        
        return {
            "makespan_days": makespan.days,
            "total_submissions": len(schedule),
            "avg_start_date": sum(schedule.values(), start=date.min).days / len(schedule)
        } 