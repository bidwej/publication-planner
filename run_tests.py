#!/usr/bin/env python3
"""Test runner script that properly sets up the Python path."""

import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
import os
os.environ['PYTHONPATH'] = f"{project_root}:{project_root}/src:{project_root}/app"

# Run pytest with the correct environment
cmd = [
    sys.executable, "-m", "pytest",
    "tests/app/",
    "-v",
    "--tb=short",
    "--import-mode=prepend"
]

print(f"Running: {' '.join(cmd)}")
print(f"Python path: {sys.path[:3]}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

result = subprocess.run(cmd, cwd=project_root)
sys.exit(result.returncode)
