"""
Gantt chart date formatting and tick generation.
Handles multi-line labels, smart spacing, and timeline visualization for Gantt charts.
"""

from datetime import date, timedelta
from typing import List, Tuple, Dict
from enum import Enum


class GanttFormat(Enum):
    """Gantt chart format types for different date ranges."""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


def format_date_display(date_obj: date, format_str: str = "%Y-%m-%d") -> str:
    """Simple date formatting function."""
    if date_obj is None:
        return "N/A"
    return date_obj.strftime(format_str)


class GanttFormatter:
    """Handles Gantt chart-specific date formatting and tick generation."""
    
    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date
        self.timeline_days = (end_date - start_date).days
    
    def get_axis_config(self) -> Dict:
        """Get x-axis configuration for the Gantt chart."""
        tick_positions, tick_labels = self.create_smart_ticks()
        
        return {
            'title': 'Timeline',
            'showgrid': True,
            'gridcolor': 'lightgray',
            'tickmode': 'array',
            'tickvals': tick_positions,
            'ticktext': tick_labels,
            'range': [0, self.timeline_days],
            'tickangle': 0,
            'tickfont': {'size': 10}
        }
    
    def get_margin_config(self) -> Dict:
        """Get margin configuration for better label display."""
        return {
            'l': 50,
            'r': 50,
            't': 80,
            'b': 80  # Increased bottom margin for multi-line labels
        }
    
    def create_smart_ticks(self) -> Tuple[List[int], List[str]]:
        """Create smart tick positions and labels to avoid overlap."""
        format_type = self._determine_format_type()
        spacing_days = self._get_spacing_days(format_type)
        
        tick_positions = []
        tick_labels = []
        
        current_date = self.start_date
        current_day = 0
        
        while current_day <= self.timeline_days:
            tick_positions.append(current_day)
            label = self._create_label(current_date, format_type)
            tick_labels.append(label)
            
            current_date += timedelta(days=spacing_days)
            current_day += spacing_days
        
        return tick_positions, tick_labels
    
    def _determine_format_type(self) -> GanttFormat:
        """Determine the appropriate format type based on timeline length."""
        if self.timeline_days <= 90:  # 3 months or less
            return GanttFormat.WEEKLY
        elif self.timeline_days <= 365:  # 1 year or less
            return GanttFormat.BIWEEKLY
        elif self.timeline_days <= 1095:  # 3 years or less
            return GanttFormat.MONTHLY
        else:  # More than 3 years
            return GanttFormat.QUARTERLY
    
    def _get_spacing_days(self, format_type: GanttFormat) -> int:
        """Get the number of days between ticks based on format type."""
        spacing_map = {
            GanttFormat.WEEKLY: 7,
            GanttFormat.BIWEEKLY: 14,
            GanttFormat.MONTHLY: 30,
            GanttFormat.QUARTERLY: 90
        }
        return spacing_map[format_type]
    
    def _create_label(self, date_obj: date, format_type: GanttFormat) -> str:
        """Create multi-line label based on format type."""
        if format_type == GanttFormat.WEEKLY:
            return self._create_weekly_label(date_obj)
        elif format_type == GanttFormat.BIWEEKLY:
            return self._create_biweekly_label(date_obj)
        elif format_type == GanttFormat.MONTHLY:
            return self._create_monthly_label(date_obj)
        else:  # QUARTERLY
            return self._create_quarterly_label(date_obj)
    
    def _create_weekly_label(self, date_obj: date) -> str:
        """Create weekly label with multi-line format."""
        week_num = (date_obj - self.start_date).days // 7 + 1
        return f"Week {week_num}<br>{format_date_display(date_obj, '%m/%d')}"
    
    def _create_biweekly_label(self, date_obj: date) -> str:
        """Create bi-weekly label with multi-line format."""
        week_num = (date_obj - self.start_date).days // 7 + 1
        return f"W{week_num}<br>{format_date_display(date_obj, '%m/%d')}"
    
    def _create_monthly_label(self, date_obj: date) -> str:
        """Create monthly label with multi-line format."""
        month_name = date_obj.strftime('%b')
        year = date_obj.year
        return f"{month_name}<br>{year}"
    
    def _create_quarterly_label(self, date_obj: date) -> str:
        """Create quarterly label with multi-line format."""
        quarter = (date_obj.month - 1) // 3 + 1
        year = date_obj.year
        return f"Q{quarter}<br>{year}"
