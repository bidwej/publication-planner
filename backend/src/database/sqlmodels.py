"""
SQLite database models for Paper Planner using SQLModel ORM.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy.sql import func
from database.session import engine as default_engine

# Database Models
class ScheduleBase(SQLModel):
    """Base model for schedules."""
    name: str = Field(index=True)
    strategy: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": func.now()})

class Schedule(ScheduleBase, table=True):
    """Schedule table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

class ScheduleItemBase(SQLModel):
    """Base model for schedule items."""
    submission_id: str = Field(index=True)
    start_date: date
    end_date: Optional[date] = None
    duration_days: int = Field(default=30)
    row_position: int = Field(default=0)

class ScheduleItem(ScheduleItemBase, table=True):
    """Schedule item table model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: Optional[int] = Field(default=None, foreign_key="schedule.id")

class ConfigurationBase(SQLModel):
    """Base model for configurations."""
    name: str = Field(index=True)
    config_data: str  # JSON string

class Configuration(ConfigurationBase, table=True):
    """Configuration table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

# Database Manager
class ScheduleDatabase:
    """SQLModel-based database manager for Paper Planner."""
    
    def __init__(self, engine=None):
        """Initialize database connection."""
        if engine is None:
            self.engine = default_engine
        else:
            self.engine = engine
    
    def save_schedule(self, name: str, strategy: str, schedule: Schedule, 
                     config: Dict[str, Any]) -> int:
        """Save a schedule to the database."""
        with Session(self.engine) as session:
            # Create schedule
            schedule_obj = Schedule(name=name, strategy=strategy)
            session.add(schedule_obj)
            session.commit()
            session.refresh(schedule_obj)
            
            schedule_id = schedule_obj.id
            if schedule_id is None:
                raise RuntimeError("Failed to get schedule ID")
            
            # Create schedule items
            for submission_id, interval in schedule.intervals.items():
                end_date = interval.start_date + timedelta(days=30)
                item = ScheduleItem(
                    schedule_id=schedule_id,
                    submission_id=submission_id,
                    start_date=interval.start_date,
                    end_date=end_date,
                    duration_days=30,
                    row_position=0
                )
                session.add(item)
            
            # Create configuration
            config_json = json.dumps(config, default=str)
            config_obj = Configuration(
                name=f"{name}_config",
                config_data=config_json
            )
            session.add(config_obj)
            
            session.commit()
            return schedule_id
    
    def load_schedule(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """Load a schedule from the database."""
        with Session(self.engine) as session:
            # Get schedule
            schedule = session.get(Schedule, schedule_id)
            if not schedule:
                return None
            
            # Get schedule items
            statement = select(ScheduleItem).where(ScheduleItem.schedule_id == schedule_id)
            items = session.exec(statement).all()
            
            schedule_dict = {}
            for item in items:
                schedule_dict[item.submission_id] = item.start_date
            
            # Get configuration
            config_statement = select(Configuration).where(Configuration.name == f"{schedule.name}_config")
            config_obj = session.exec(config_statement).first()
            config = json.loads(config_obj.config_data) if config_obj else {}
            
            return {
                'id': schedule_id,
                'name': schedule.name,
                'strategy': schedule.strategy,
                'created_at': schedule.created_at,
                'schedule': schedule_dict,
                'config': config
            }
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all available schedules."""
        with Session(self.engine) as session:
            statement = select(Schedule).order_by(Schedule.created_at.desc())
            schedules = session.exec(statement).all()
            
            return [
                {
                    'id': s.id,
                    'name': s.name,
                    'strategy': s.strategy,
                    'created_at': s.created_at,
                    'updated_at': s.updated_at
                }
                for s in schedules
            ]
    
    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule from the database."""
        try:
            with Session(self.engine) as session:
                # Get schedule
                schedule = session.get(Schedule, schedule_id)
                if not schedule:
                    return False
                
                # Delete related items
                statement = select(ScheduleItem).where(ScheduleItem.schedule_id == schedule_id)
                items = session.exec(statement).all()
                for item in items:
                    session.delete(item)
                
                # Delete configuration
                config_statement = select(Configuration).where(Configuration.name == f"{schedule.name}_config")
                config_obj = session.exec(config_statement).first()
                if config_obj:
                    session.delete(config_obj)
                
                # Delete schedule
                session.delete(schedule)
                session.commit()
                return True
        except Exception:
            return False
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
