#!/usr/bin/env python3
"""Simple test script to verify imports work."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.main import main, create_dashboard_app, create_timeline_app
    print("✅ app.main imports successful!")
except ImportError as e:
    print(f"❌ app.main import failed: {e}")

try:
    from app.models import WebAppState
    print("✅ app.models imports successful!")
except ImportError as e:
    print(f"❌ app.models import failed: {e}")

try:
    from src.core.models import Config, Submission
    print("✅ src.core.models imports successful!")
except ImportError as e:
    print(f"❌ src.core.models import failed: {e}")

print(f"Python path: {sys.path[:3]}")
print(f"Python executable: {sys.executable}")
