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
    from app.main import app
    
    if __name__ == "__main__":
        print("🚀 Starting Paper Planner Dashboard...")
        print("📊 Dashboard will be available at: http://127.0.0.1:8050")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the app
        app.run(
            debug=False,
            host='127.0.0.1',
            port=8050
        )
        
except ImportError as e:
    print(f"❌ Error importing dashboard app: {e}")
    print("💡 Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting dashboard: {e}")
    sys.exit(1)
