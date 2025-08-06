#!/usr/bin/env python3
"""
Runner script for the Paper Planner Dashboard.
This runs the full dashboard with all features.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.main import main
    
    if __name__ == "__main__":
        # Set up arguments for dashboard mode
        sys.argv = ['main.py', '--mode', 'dashboard', '--debug', 'False']
        
        # Run the main function
        main()
        
except ImportError as e:
    print(f"❌ Error importing dashboard app: {e}")
    print("💡 Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting dashboard: {e}")
    sys.exit(1)
