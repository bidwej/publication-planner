"""
Storage module for the Paper Planner web application.
Handles SQLite-based localStorage equivalent for schedules.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.core.models import ScheduleState


class ScheduleStorage:
    """SQLite-based storage for schedules (localStorage equivalent)."""
    
    def __init__(self):
        """Initialize storage with SQLite database in user's home directory."""
        self._init_storage()
    
    def _init_storage(self):
        """Initialize SQLite storage."""
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
            schedule_data = schedule_state.to_dict()
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
                    return ScheduleState.from_dict(data)
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
            schedule_data = schedule_state.to_dict()
            schedule_data['filename'] = filename
            return json.dumps(schedule_data, indent=2)
        except Exception as e:
            print("Error exporting schedule: %s", e)
            return ""
    
    def import_schedule(self, json_data: str) -> Optional[ScheduleState]:
        """Import schedule from JSON string."""
        try:
            data = json.loads(json_data)
            return ScheduleState.from_dict(data)
        except Exception as e:
            print("Error importing schedule: %s", e)
            return None


class StorageManager:
    """Manager class for storage operations."""
    
    def __init__(self):
        """Initialize storage manager."""
        self.storage = ScheduleStorage()
    
    def save_schedule(self, schedule_data: Dict[str, Any], filename: str) -> str:
        """Save schedule data."""
        try:
            # Convert dict to ScheduleState if needed
            if isinstance(schedule_data, dict):
                schedule_state = ScheduleState.from_dict(schedule_data)
            else:
                schedule_state = schedule_data
            
            success = self.storage.save_schedule(schedule_state, filename)
            return filename if success else ""
        except Exception as e:
            print("Error saving schedule: %s", e)
            return ""
    
    def load_schedule(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load schedule data."""
        try:
            schedule_state = self.storage.load_schedule(filename)
            if schedule_state:
                return schedule_state.to_dict()
            return None
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
