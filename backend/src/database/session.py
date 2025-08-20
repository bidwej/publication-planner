"""
Database session management for Paper Planner.
"""

from sqlmodel import create_engine, Session, SQLModel
from pathlib import Path
import os

# Database path - works from both backend/ and frontend/ directories
# From backend/: points to ../schedules.db (project root)
# From frontend/: points to ../schedules.db (project root) 
# From root/: points to ./schedules.db (current directory)
DATABASE_PATH = Path("schedules.db") if Path("backend").exists() and Path("frontend").exists() else Path("../schedules.db")

# Create engine
engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)

def get_session():
    """Get a database session."""
    return Session(engine)

def create_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
