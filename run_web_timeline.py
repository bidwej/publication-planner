#!/usr/bin/env python3
"""
Simple runner for the Paper Planner Timeline application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    try:
        # Import and run the main module with timeline mode
        from app.main import main
        
        # Set sys.argv to specify timeline mode
        sys.argv = ['main.py', '--mode', 'timeline']
        
        main()
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
