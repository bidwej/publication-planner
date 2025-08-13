"""
Gantt chart date formatting and tick generation.
Handles multi-line labels, smart spacing, and timeline visualization for Gantt charts.
"""

from datetime import date, timedelta
from typing import List, Tuple, Dict, Optional
from enum import Enum

from src.core.models import Submission, SubmissionType, ConferenceType


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


class GanttStyler:
    """Handles all styling for Gantt chart elements."""
    
    # Color scheme for different submission types
    COLORS = {
        SubmissionType.ABSTRACT: "#FF6B6B",      # Red for abstracts
        SubmissionType.PAPER: "#4ECDC4",         # Teal for papers
        SubmissionType.POSTER: "#45B7D1",        # Blue for posters
        # Note: MODs are actually SubmissionType.PAPER with author="pccp"
        # Work items would be SubmissionType.ABSTRACT or other types
    }
    
    # Border colors for medical vs engineering
    BORDER_COLORS = {
        ConferenceType.MEDICAL: "#E74C3C",       # Red border for medical
        ConferenceType.ENGINEERING: "#3498DB",   # Blue border for engineering
    }
    
    # Default colors for author types
    AUTHOR_COLORS = {
        "pccp": "#2E86AB",                       # Blue for PCCP
        "ed": "#A23B72",                         # Purple for ED
    }
    
    @classmethod
    def get_submission_color(cls, submission: Submission) -> str:
        """Get the base color for a submission based on its type and author."""
        # For MODs (PCCP papers), use the author color
        if submission.author == "pccp":
            return cls.AUTHOR_COLORS["pccp"]
        elif submission.author == "ed":
            return cls.AUTHOR_COLORS["ed"]
        
        # Otherwise use the submission type color
        return cls.COLORS.get(submission.kind, "#95A5A6")  # Default gray
    
    @classmethod
    def get_border_color(cls, submission: Submission, config) -> Optional[str]:
        """Get border color based on conference type (medical vs engineering)."""
        if not submission.conference_id:
            return None
        
        conference = config.conferences_dict.get(submission.conference_id)
        if not conference:
            return None
        
        return cls.BORDER_COLORS.get(conference.conf_type)
    
    @classmethod
    def get_author_color(cls, submission: Submission) -> str:
        """Get color based on author type (PCCP vs ED)."""
        if submission.author in cls.AUTHOR_COLORS:
            return cls.AUTHOR_COLORS[submission.author]
        return cls.get_submission_color(submission)
    
    @classmethod
    def get_legend_items(cls) -> List[Tuple[str, str, str]]:
        """Get legend items with labels, colors, and descriptions."""
        return [
            ("PCCP MODs", cls.AUTHOR_COLORS["pccp"], "PCCP MOD submissions"),
            ("ED Papers", cls.AUTHOR_COLORS["ed"], "ED Paper submissions"),
            ("Abstracts", cls.COLORS[SubmissionType.ABSTRACT], "Abstract submissions"),
            ("Papers", cls.COLORS[SubmissionType.PAPER], "Paper submissions"),
            ("Posters", cls.COLORS[SubmissionType.POSTER], "Poster submissions"),
            ("Medical Border", cls.BORDER_COLORS[ConferenceType.MEDICAL], "Medical conference submissions"),
            ("Engineering Border", cls.BORDER_COLORS[ConferenceType.ENGINEERING], "Engineering conference submissions"),
        ]
    
    @classmethod
    def get_matching_border_color(cls, submission: Submission, config) -> Optional[str]:
        """Get border color for submissions that should have matching borders (abstract-paper pairs)."""
        if not submission.conference_id:
            return None
        
        conference = config.conferences_dict.get(submission.conference_id)
        if not conference or not conference.requires_abstract_before_paper():
            return None
        
        # For conferences requiring abstracts before papers, use a special color
        return "#9B59B6"  # Purple for matching abstract-paper pairs


class GanttFormatter:
    """Handles Gantt chart-specific date formatting and tick generation."""
    
    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date
        self.timeline_days = (end_date - start_date).days
    
    def get_axis_config(self) -> Dict:
        """Get primary x-axis configuration (quarters) - positioned at bottom."""
        quarter_positions, quarter_labels = self.create_quarter_ticks()
        
        return {
            'title': 'Timeline (Quarters)',
            'showgrid': True,
            'gridcolor': 'lightgray',
            'tickmode': 'array',
            'tickvals': quarter_positions,
            'ticktext': quarter_labels,
            'range': [0, self.timeline_days],
            'tickangle': 0,
            'tickfont': {'size': 11, 'color': 'darkblue'},
            'side': 'bottom',
            'position': 0.05,
            'anchor': 'y'
        }
    
    def get_year_annotations(self) -> List[Dict]:
        """Get year annotations to place below the x-axis."""
        year_positions, year_labels = self.create_year_ticks()
        annotations = []
        
        for pos, label in zip(year_positions, year_labels):
            annotations.append({
                'x': pos,
                'y': -0.1,  # Below the axis
                'text': label,
                'showarrow': False,
                'xref': 'x',
                'yref': 'paper',
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 12, 'color': 'darkred', 'weight': 'bold'},
                'bgcolor': 'rgba(255, 255, 255, 0.8)',
                'bordercolor': 'darkred',
                'borderwidth': 1
            })
        
        return annotations
    
    def get_secondary_axis_config(self) -> Dict:
        """Get secondary x-axis configuration with years below quarters."""
        year_positions, year_labels = self.create_year_ticks()
        
        return {
            'title': 'Years',
            'showgrid': False,
            'tickmode': 'array',
            'tickvals': year_positions,
            'ticktext': year_labels,
            'range': [0, self.timeline_days],
            'tickangle': 0,
            'tickfont': {'size': 12, 'color': 'darkred', 'weight': 'bold'},
            'overlaying': 'x',
            'side': 'bottom',
            'position': 0.15,
            'anchor': 'y'
        }
    
    def get_tertiary_axis_config(self) -> Dict:
        """Get tertiary x-axis configuration with years on bottom."""
        year_positions, year_labels = self.create_year_ticks()
        
        return {
            'title': 'Years',
            'showgrid': False,
            'tickmode': 'array',
            'tickvals': year_positions,
            'ticktext': year_labels,
            'range': [0, self.timeline_days],
            'tickangle': 0,
            'tickfont': {'size': 12, 'color': 'darkred', 'weight': 'bold'},
            'overlaying': 'x',
            'side': 'bottom',
            'position': 0.25,
            'anchor': 'y'
        }
    
    def create_quarter_ticks(self) -> Tuple[List[int], List[str]]:
        """Create quarter tick positions and labels."""
        tick_positions = []
        tick_labels = []
        
        # Generate ticks for each quarter in the timeline
        start_year = self.start_date.year
        end_year = self.end_date.year
        
        for year in range(start_year, end_year + 1):
            # Quarter ticks (January 1st, April 1st, July 1st, October 1st)
            for month in [1, 4, 7, 10]:
                quarter_date = date(year, month, 1)
                if quarter_date >= self.start_date and quarter_date <= self.end_date:
                    day_offset = (quarter_date - self.start_date).days
                    quarter = (month - 1) // 3 + 1
                    tick_positions.append(day_offset)
                    tick_labels.append(f"Q{quarter}")
        
        return tick_positions, tick_labels
    
    def create_year_ticks(self) -> Tuple[List[int], List[str]]:
        """Create year tick positions and labels."""
        tick_positions = []
        tick_labels = []
        
        # Generate ticks for each year in the timeline
        start_year = self.start_date.year
        end_year = self.end_date.year
        
        for year in range(start_year, end_year + 1):
            # Year tick (January 1st)
            year_start = date(year, 1, 1)
            if year_start >= self.start_date and year_start <= self.end_date:
                day_offset = (year_start - self.start_date).days
                tick_positions.append(day_offset)
                tick_labels.append(f"{year}")
        
        return tick_positions, tick_labels
    
    def get_margin_config(self) -> Dict:
        """Get margin configuration for better label display with annotations."""
        return {
            'l': 50,   # Left margin
            'r': 50,   # Right margin
            't': 80,   # Top margin
            'b': 120   # Bottom margin for annotations
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
        """Create label based on format type."""
        if format_type == GanttFormat.WEEKLY:
            return self._create_weekly_label(date_obj)
        elif format_type == GanttFormat.BIWEEKLY:
            return self._create_biweekly_label(date_obj)
        elif format_type == GanttFormat.MONTHLY:
            return self._create_monthly_label(date_obj)
        else:  # QUARTERLY
            return self._create_quarterly_label(date_obj)
    
    def _create_weekly_label(self, date_obj: date) -> str:
        """Create weekly label."""
        return format_date_display(date_obj, '%m/%d')
    
    def _create_biweekly_label(self, date_obj: date) -> str:
        """Create bi-weekly label."""
        return format_date_display(date_obj, '%m/%d')
    
    def _create_monthly_label(self, date_obj: date) -> str:
        """Create monthly label."""
        return format_date_display(date_obj, '%b %Y')
    
    def _create_quarterly_label(self, date_obj: date) -> str:
        """Create quarterly label."""
        quarter = (date_obj.month - 1) // 3 + 1
        year = date_obj.year
        return f"Q{quarter} {year}"
