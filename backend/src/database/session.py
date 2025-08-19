"""
Database session management for Paper Planner.
"""

from sqlmodel import create_engine, Session
from pathlib import Path

import os
from dotenv import load_dotenv

# Load environment variables (optional)
try:
    load_dotenv()
except Exception:
    # If .env file is missing or corrupted, use defaults
    pass

# Database path from environment variable
DATABASE_PATH = os.getenv("DATABASE_PATH", "../schedules.db")

# Create engine
engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)

def get_session():
    """Get a database session."""
    return Session(engine)

def create_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
