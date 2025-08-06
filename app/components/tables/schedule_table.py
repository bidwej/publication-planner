"""
Schedule table component for displaying schedule data.
"""

from typing import Dict, List, Any
from datetime import date
from core.models import Config
from src.output.tables import (
    create_schedule_table,
    create_violations_table,
    create_metrics_table,
    create_analytics_table
)

# Re-export the consolidated functions for backward compatibility
__all__ = [
    'create_schedule_table',
    'create_violations_table', 
    'create_metrics_table',
    'create_analytics_table'
]
