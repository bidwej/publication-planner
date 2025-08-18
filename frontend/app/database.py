"""
Frontend database module for reading schedule data from backend SQLite database.
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import date
import json

def get_database_path() -> str:
    """Get the database path from environment or default to project root."""
    # Try to get from .env file first
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_PATH='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
    
    # Default to project root
    project_root = Path(__file__).parent.parent.parent
    return str(project_root / "schedules.db")

def get_schedule_data() -> Optional[Dict[str, Any]]:
    """Get schedule data from the backend database."""
    try:
        db_path = get_database_path()
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}")
            return None
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the most recent schedule
        cursor.execute("""
            SELECT s.id, s.name, s.strategy, s.schedule_data, s.config_data, s.created_at
            FROM schedules s
            ORDER BY s.created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("No schedules found in database")
            return None
        
        schedule_id, name, strategy, schedule_data, config_data, created_at = row
        
        # Parse the JSON data
        schedule = json.loads(schedule_data) if schedule_data else {}
        config = json.loads(config_data) if config_data else {}
        
        conn.close()
        
        return {
            'id': schedule_id,
            'name': name,
            'strategy': strategy,
            'schedule': schedule,
            'config': config,
            'created_at': created_at
        }
        
    except Exception as e:
        print(f"Error reading from database: {e}")
        return None

def list_schedules() -> List[Dict[str, Any]]:
    """List all available schedules in the database."""
    try:
        db_path = get_database_path()
        if not os.path.exists(db_path):
            return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, strategy, created_at
            FROM schedules
            ORDER BY created_at DESC
        """)
        
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'id': row[0],
                'name': row[1],
                'strategy': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        return schedules
        
    except Exception as e:
        print(f"Error listing schedules: {e}")
        return []

def get_schedule_by_id(schedule_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific schedule by ID."""
    try:
        db_path = get_database_path()
        if not os.path.exists(db_path):
            return None
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, s.name, s.strategy, s.schedule_data, s.config_data, s.created_at
            FROM schedules s
            WHERE s.id = ?
        """, (schedule_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        schedule_id, name, strategy, schedule_data, config_data, created_at = row
        
        # Parse the JSON data
        schedule = json.loads(schedule_data) if schedule_data else {}
        config = json.loads(config_data) if config_data else {}
        
        conn.close()
        
        return {
            'id': schedule_id,
            'name': name,
            'strategy': strategy,
            'schedule': schedule,
            'config': config,
            'created_at': created_at
        }
        
    except Exception as e:
        print(f"Error reading schedule {schedule_id}: {e}")
        return None
