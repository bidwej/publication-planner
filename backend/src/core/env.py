"""Environment configuration utilities."""

import os
import sys
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")


def setup_python_path() -> bool:
    """Set up Python path for backend imports."""
    # Load .env file first
    load_env_file()
    
    # Get PYTHONPATH from environment
    python_path = os.getenv('PYTHONPATH', 'src')
    backend_root = os.getenv('BACKEND_ROOT', '.')
    
    # Determine the backend directory
    if backend_root == '.':
        backend_dir = Path(__file__).parent.parent.parent
    else:
        backend_dir = Path(backend_root)
    
    # Add Python path
    src_path = backend_dir / python_path
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        os.environ['PYTHONPATH'] = str(src_path)
        return True
    
    return False


def setup_backend_environment() -> bool:
    """Set up the complete backend environment."""
    try:
        # Set up Python path
        if not setup_python_path():
            print("❌ Failed to set up Python path")
            return False
        
        # Test imports
        from core.models import Config
        from core.config import load_config
        print("✓ Backend environment ready")
        return True
        
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
        return False
