"""
Storage module for the Paper Planner web application.
Handles SQLite-based localStorage equivalent for schedules.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.models import ScheduleState, Config
from datetime import datetime


class ScheduleStorage:
    """SQLite-based storage for schedules (localStorage equivalent)."""
    
    def __init__(self):
        """Initialize storage with SQLite database in user's home directory."""
        try:
            # Create data directory in user's home folder (client-side equivalent)
            data_dir = Path.home() / ".paper_planner"
            data_dir.mkdir(exist_ok=True)
            
            self.db_path = data_dir / "schedules.db"
            
            # Create table if it doesn't exist
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schedules (
                        filename TEXT PRIMARY KEY,
                        schedule_data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        submission_count INTEGER NOT NULL
                    )
                """)
                conn.commit()
        except Exception as e:
            print("Warning: Could not initialize storage: %s", e)
            self.db_path = None
    
    def save_schedule(self, schedule_state: ScheduleState, filename: str) -> bool:
        """Save schedule to SQLite storage."""
        if not self.db_path:
            return False
            
        try:
            schedule_data = schedule_state.model_dump()
            json_data = json.dumps(schedule_data)
            
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO schedules 
                    (filename, schedule_data, timestamp, strategy, submission_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    filename,
                    json_data,
                    schedule_state.timestamp,
                    schedule_state.strategy.value,
                    len(schedule_state.schedule)
                ))
                conn.commit()
            
            return True
        except Exception as e:
            print("Error saving schedule: %s", e)
            return False
    
    def load_schedule(self, filename: str) -> Optional[ScheduleState]:
        """Load schedule from SQLite storage."""
        if not self.db_path:
            return None
            
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT schedule_data FROM schedules WHERE filename = ?",
                    (filename,)
                )
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row[0])
                    return ScheduleState.model_validate(data)
                return None
        except Exception as e:
            print("Error loading schedule: %s", e)
            return None
    
    def list_saved_schedules(self) -> List[Dict[str, Any]]:
        """List all saved schedules from SQLite storage."""
        if not self.db_path:
            return []
            
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("""
                    SELECT filename, timestamp, strategy, submission_count 
                    FROM schedules 
                    ORDER BY timestamp DESC
                """)
                
                schedules = []
                for row in cursor.fetchall():
                    schedules.append({
                        "filename": row[0],
                        "timestamp": row[1],
                        "strategy": row[2],
                        "submission_count": row[3]
                    })
                
                return schedules
        except Exception as e:
            print("Error listing saved schedules: %s", e)
            return []
    
    def delete_schedule(self, filename: str) -> bool:
        """Delete a saved schedule."""
        if not self.db_path:
            return False
            
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM schedules WHERE filename = ?", (filename,))
                conn.commit()
            
            return True
        except Exception as e:
            print("Error deleting schedule: %s", e)
            return False
    
    def export_schedule(self, schedule_state: ScheduleState, filename: str) -> str:
        """Export schedule as downloadable JSON string."""
        try:
            # Add filename to the exported data
            export_data = schedule_state.model_dump()
            export_data['filename'] = filename
            return json.dumps(export_data, indent=2)
        except Exception as e:
            print("Error exporting schedule: %s", e)
            return ""
    
    def import_schedule(self, json_data: str) -> Optional[ScheduleState]:
        """Import schedule from JSON string."""
        try:
            data = json.loads(json_data)
            return ScheduleState.model_validate(data)
        except Exception as e:
            print("Error importing schedule: %s", e)
            return None


class StorageManager:
    """Manager class for storage operations."""
    
    def __init__(self):
        """Initialize storage manager."""
        self.storage = ScheduleStorage()
    
    def save_schedule(self, schedule_state: ScheduleState, filename: str) -> str:
        """Save schedule data directly."""
        try:
            success = self.storage.save_schedule(schedule_state, filename)
            return filename if success else ""
        except Exception as e:
            print("Error saving schedule: %s", e)
            return ""
    
    def load_schedule(self, filename: str) -> Optional[ScheduleState]:
        """Load schedule data directly as ScheduleState."""
        try:
            return self.storage.load_schedule(filename)
        except Exception as e:
            print("Error loading schedule: %s", e)
            return None
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all saved schedules."""
        try:
            return self.storage.list_saved_schedules()
        except Exception as e:
            print("Error listing schedules: %s", e)
            return []
    
    def delete_schedule(self, filename: str) -> bool:
        """Delete a saved schedule."""
        try:
            return self.storage.delete_schedule(filename)
        except Exception as e:
            print("Error deleting schedule: %s", e)
            return False


# Component state storage using SQLite (consistent with schedule storage)
def save_state(component_name: str, state_data: Dict[str, Any]) -> bool:
    """Save component state to SQLite storage.
    
    Args:
        component_name: Name of the component (e.g., 'dashboard', 'gantt', 'metrics')
        state_data: State data to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        data_dir = Path.home() / ".paper_planner"
        data_dir.mkdir(exist_ok=True)
        
        db_path = data_dir / "component_states.db"
        
        with sqlite3.connect(str(db_path)) as conn:
            # Create component states table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS component_states (
                    component_name TEXT,
                    state_key TEXT,
                    state_value TEXT,
                    timestamp TEXT,
                    PRIMARY KEY (component_name, state_key)
                )
            """)
            
            # Save each state key-value pair
            timestamp = datetime.now().isoformat()
            for key, value in state_data.items():
                if key != 'timestamp':  # Don't save timestamp as a state key
                    conn.execute("""
                        INSERT OR REPLACE INTO component_states 
                        (component_name, state_key, state_value, timestamp)
                        VALUES (?, ?, ?, ?)
                    """, (component_name, key, json.dumps(value), timestamp))
            
            conn.commit()
        return True
    except Exception as e:
        print(f"Error saving {component_name} state: {e}")
        return False


def load_state(component_name: str) -> Dict[str, Any]:
    """Load component state from SQLite storage.
    
    Args:
        component_name: Name of the component (e.g., 'dashboard', 'gantt', 'metrics')
    
    Returns:
        State data dictionary, or empty dict if not found
    """
    try:
        data_dir = Path.home() / ".paper_planner"
        db_path = data_dir / "component_states.db"
        
        if not db_path.exists():
            return {}
        
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute("""
                SELECT state_key, state_value, timestamp 
                FROM component_states 
                WHERE component_name = ?
                ORDER BY timestamp DESC
            """, (component_name,))
            
            state_data = {}
            latest_timestamp = None
            for row in cursor.fetchall():
                key, value, timestamp = row
                latest_timestamp = timestamp
                try:
                    state_data[key] = json.loads(value)
                except json.JSONDecodeError:
                    state_data[key] = value  # Fallback to raw value
            
            if state_data and latest_timestamp:
                state_data['timestamp'] = latest_timestamp
            
            return state_data
    except Exception as e:
        print(f"Error loading {component_name} state: {e}")
        return {}


class StateManager:
    """Clean state manager for components."""
    
    def __init__(self):
        """Initialize state manager."""
        pass
    
    def save_component_state(self, component_name: str, config: Optional[Config] = None, 
                           chart_type: str = 'timeline', custom_settings: Optional[Dict[str, Any]] = None,
                           schedule: Optional[Dict[str, Any]] = None) -> bool:
        """Save component state with proper separation of concerns.
        
        Args:
            component_name: Name of the component
            config: Configuration object (optional)
            chart_type: Current chart type
            custom_settings: Any custom component settings
            schedule: Schedule data for timeline display (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            state_data = {
                'chart_type': chart_type,
                'last_refresh': datetime.now().isoformat(),
                'custom_settings': custom_settings or {}
            }
            
            # Store essential config data
            if config:
                state_data['config_data'] = {
                    'submission_count': len(config.submissions),
                    'conference_count': len(config.conferences),
                    'min_abstract_lead_time_days': config.min_abstract_lead_time_days,
                    'min_paper_lead_time_days': config.min_paper_lead_time_days,
                    'max_concurrent_submissions': config.max_concurrent_submissions,
                    'config': config,  # Store the full config for timeline
                    'schedule': schedule  # Store the schedule data for timeline
                }
            
            return save_state(component_name, state_data)
        except Exception as e:
            print(f"Error saving component state: {e}")
            return False
    
    def load_component_state(self, component_name: str) -> Dict[str, Any]:
        """Load component state.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Component state data
        """
        return load_state(component_name)
    
    def get_component_config_summary(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of stored config data for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Config summary or None if not found
        """
        state = self.load_component_state(component_name)
        return state.get('config_data')
    
    def update_component_refresh_time(self, component_name: str) -> bool:
        """Update the last refresh time for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_state = self.load_component_state(component_name)
            current_state['last_refresh'] = datetime.now().isoformat()
            return save_state(component_name, current_state)
        except Exception as e:
            print(f"Error updating refresh time: {e}")
            return False


# Global state manager instance - lazy loaded to avoid import-time issues
_state_manager_instance = None

def get_state_manager():
    """Get the global state manager instance, creating it if needed."""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance
