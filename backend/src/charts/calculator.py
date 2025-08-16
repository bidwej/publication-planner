"""
Chart calculation logic for gantt charts.

This module handles the business logic for building gantt chart data structures.
Pure business logic - no web framework dependencies.
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from core.models import Config, Submission


class ChartCalculator:
    """Calculates chart data structure from schedule and config."""
    
    def __init__(self, schedule: Dict[str, date], config: Config, forced_timeline: Optional[Dict] = None):
        self.schedule = schedule
        self.config = config
        
        # Handle forced timeline range if specified
        if forced_timeline and forced_timeline.get("force_timeline_range"):
            self.min_date = forced_timeline["timeline_start"]
            self.max_date = forced_timeline["timeline_end"]
            self.timeline_start = forced_timeline["timeline_start"]
        else:
            # Calculate dates naturally from schedule
            self.min_date = min(schedule.values()) if schedule else date.today()
            if schedule:
                max_start = max(schedule.values())
                max_end_date = max_start
                for submission_id, start_date in schedule.items():
                    submission = config.submissions_dict.get(submission_id)
                    if submission:
                        duration = submission.get_duration_days(config)
                        if duration <= 0:
                            duration = 7
                        end_date = start_date + timedelta(days=duration)
                        if end_date > max_end_date:
                            max_end_date = end_date
                
                self.max_date = max_end_date + timedelta(days=30)
            else:
                self.max_date = date.today()
            self.timeline_start = self.min_date
        
        # Initialize chart properties
        self.bar_height = 1.2
        self.y_margin = self.bar_height / 2 + 0.2
        
        # Calculate concurrency levels
        self.concurrency_map = self._calculate_simple_concurrency()
        self.max_concurrency = max(self.concurrency_map.values()) if self.concurrency_map else 0
    
    def _calculate_simple_concurrency(self) -> Dict[str, int]:
        """Calculate concurrency levels simply: start at row 0, only go to row 1 if overlap."""
        concurrency_map = {}
        
        # Sort submissions by start date to process them chronologically
        sorted_schedule = sorted(self.schedule.items(), key=lambda x: x[1])
        
        for submission_id, start_date in sorted_schedule:
            submission = self.config.submissions_dict.get(submission_id)
            if not submission:
                continue
            
            # Calculate end date
            duration_days = submission.get_duration_days(self.config)
            if duration_days <= 0:
                duration_days = 7
            end_date = start_date + timedelta(days=duration_days)
            
            # Find the lowest available row (start at 0)
            row = 0
            while self._row_has_overlap(row, start_date, end_date, submission_id, concurrency_map):
                row += 1
            
            concurrency_map[submission_id] = row
        
        return concurrency_map
    
    def _row_has_overlap(self, row: int, start_date: date, end_date: date, 
                         current_id: str, concurrency_map: Dict[str, int]) -> bool:
        """Check if a specific row has overlap with the current submission."""
        for other_id, other_row in concurrency_map.items():
            if other_id == current_id:
                continue
            
            if other_row == row:
                other_submission = self.config.submissions_dict.get(other_id)
                if other_submission:
                    other_duration = other_submission.get_duration_days(self.config)
                    if other_duration <= 0:
                        other_duration = 7
                    other_start = self.schedule.get(other_id)
                    if other_start:
                        other_end = other_start + timedelta(days=other_duration)
                        
                        # Check for overlap
                        if not (end_date <= other_start or start_date >= other_end):
                            return True
        
        return False
    
    def calculate_chart_data(self) -> Dict[str, Any]:
        """Calculate the complete chart data structure."""
        return {
            'min_date': self.min_date,
            'max_date': self.max_date,
            'timeline_start': self.timeline_start,
            'bar_height': self.bar_height,
            'y_margin': self.y_margin,
            'concurrency_map': self.concurrency_map,
            'max_concurrency': self.max_concurrency,
            'schedule': self.schedule,
            'config': self.config
        }
    
    def calculate_submission_data(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Calculate data for a specific submission."""
        if submission_id not in self.schedule:
            return None
        
        submission = self.config.submissions_dict.get(submission_id)
        if not submission:
            return None
        
        start_date = self.schedule[submission_id]
        duration_days = submission.get_duration_days(self.config)
        if duration_days <= 0:
            duration_days = 7
        end_date = start_date + timedelta(days=duration_days)
        row = self.concurrency_map.get(submission_id, 0)
        
        return {
            'id': submission_id,
            'title': submission.title,
            'start_date': start_date,
            'end_date': end_date,
            'duration_days': duration_days,
            'row': row,
            'engineering': submission.engineering,
            'kind': submission.kind.value,
            'conference_id': submission.conference_id
        }
