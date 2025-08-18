#!/usr/bin/env python3
"""
Test script to verify database connection and create sample data.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.session import create_tables, get_session
from database.sqlmodels import ScheduleDatabase, Schedule, ScheduleItem, Configuration
from datetime import date, datetime
import json

def test_database_connection():
    """Test basic database connection and table creation."""
    try:
        print("Testing database connection...")
        
        # Create tables
        create_tables()
        print("✓ Tables created successfully")
        
        # Test session
        session = get_session()
        print("✓ Database session created successfully")
        
        # Test database manager
        db = ScheduleDatabase()
        print("✓ ScheduleDatabase initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def create_sample_data():
    """Create sample schedule data for testing."""
    try:
        print("\nCreating sample data...")
        
        db = ScheduleDatabase()
        
        # Sample schedule data
        sample_schedule = {
            "mod_1": "2025-01-01",
            "mod_2": "2025-02-01", 
            "J1-abs": "2025-03-01",
            "J1-pap": "2025-04-15",
            "J2-abs": "2025-03-15",
            "J2-pap": "2025-05-01",
            "J3": "2025-06-01"
        }
        
        # Sample config data
        sample_config = {
            "strategy": "greedy",
            "max_concurrent": 2,
            "created_at": datetime.now().isoformat()
        }
        
        # Save to database
        schedule_id = db.save_schedule(
            name="Sample Schedule",
            strategy="greedy", 
            schedule=sample_schedule,
            config=sample_config
        )
        
        print(f"✓ Sample schedule saved with ID: {schedule_id}")
        
        # List schedules
        schedules = db.list_schedules()
        print(f"✓ Found {len(schedules)} schedules in database")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create sample data: {e}")
        return False

def main():
    """Main test function."""
    print("=== Database Connection Test ===\n")
    
    # Test connection
    if not test_database_connection():
        print("\n❌ Database test failed!")
        return False
    
    # Create sample data
    if not create_sample_data():
        print("\n❌ Sample data creation failed!")
        return False
    
    print("\n✅ All database tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
