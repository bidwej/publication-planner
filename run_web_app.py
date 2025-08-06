#!/usr/bin/env python3
"""
Entry point for the Paper Planner web application.

Run this script to start the Dash web server.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

if __name__ == "__main__":
    try:
        from app.main import app
        
        print("🚀 Starting Paper Planner Web Application...")
        print("📊 Dashboard will be available at: http://127.0.0.1:8050")
        print("🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the app
        app.run(
            debug=True,
            host='127.0.0.1',
            port=8050,
            dev_tools_hot_reload=True
        )
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
