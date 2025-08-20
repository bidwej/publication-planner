"""Frontend environment configuration utilities."""

import os
import sys
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Optional[Path] = None) -> None:
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent.parent / ".env"
    
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


def setup_backend_imports() -> bool:
    """Set up backend imports for frontend components."""
    # Load .env file first
    load_env_file()
    
    # Get backend path from environment
    backend_src_path = os.getenv('BACKEND_SRC_PATH', '../backend/src')
    frontend_root = os.getenv('FRONTEND_ROOT', '.')
    
    # Determine the frontend directory
    if frontend_root == '.':
        frontend_dir = Path(__file__).parent.parent
    else:
        frontend_dir = Path(frontend_root)
    
    # Add backend path
    backend_path = frontend_dir / backend_src_path
    if backend_path.exists() and str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
        os.environ['PYTHONPATH'] = str(backend_path)
        return True
    
    return False


def setup_frontend_environment() -> bool:
    """Set up the complete frontend environment with backend access."""
    try:
        # Set up backend imports
        if not setup_backend_imports():
            print("❌ Failed to set up backend imports")
            return False
        
        # Test backend imports
        from core.models import Config
        from core.config import load_config
        print("✓ Frontend environment ready with backend access")
        return True
        
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
        print("Frontend will run without backend functionality")
        return False


def get_dash_config() -> dict:
    """Get Dash application configuration from environment."""
    load_env_file()
    
    return {
        'host': os.getenv('DASH_HOST', '127.0.0.1'),
        'port_dashboard': int(os.getenv('DASH_PORT_DASHBOARD', '8050')),
        'port_gantt': int(os.getenv('DASH_PORT_GANTT', '8051')),
        'port_metrics': int(os.getenv('DASH_PORT_METRICS', '8052')),
        'debug': os.getenv('DEBUG', 'true').lower() == 'true'
    }
