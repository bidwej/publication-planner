#!/usr/bin/env python3
"""
Runner script for the Paper Planner Timeline.
This runs the timeline-only view with Gantt chart.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from app.main import main
    
    if __name__ == "__main__":
        # Set up arguments for timeline mode (no debug flag = debug=False)
        sys.argv = ['main.py', '--mode', 'timeline']
        
        # Run the main function
        main()
        
except ImportError as e:
    print(f"❌ Error importing timeline app: {e}")
    print("💡 Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting timeline: {e}")
    sys.exit(1)
