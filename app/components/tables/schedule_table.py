"""
Schedule table component for displaying schedule data.
"""

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
