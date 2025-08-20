#!/usr/bin/env python3
"""Development setup script for Paper Planner Backend."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False


def setup_development_environment():
    """Set up the development environment."""
    backend_dir = Path(__file__).parent
    
    print("🚀 Setting up Paper Planner Backend Development Environment")
    print(f"📁 Working directory: {backend_dir}")
    print("-" * 60)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Install in development mode
    success = run_command(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        "Installing backend package in development mode"
    )
    
    if not success:
        print("\n❌ Development setup failed!")
        return False
    
    # Test imports
    print("\n🧪 Testing imports...")
    try:
        # Test backend imports
        import core.models
        import core.config
        import schedulers.base
        print("✅ Backend imports working correctly")
        
        # Test that we can create a config
        from core.models import Config
        config = Config.create_default()
        print("✅ Backend functionality working correctly")
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    print("\n🎉 Development environment setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy env.template to .env: cp env.template .env")
    print("2. Run the backend: python run_backend.py --help")
    print("3. Run tests: pytest")
    
    return True


if __name__ == "__main__":
    success = setup_development_environment()
    sys.exit(0 if success else 1)
