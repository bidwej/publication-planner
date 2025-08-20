#!/usr/bin/env python3
"""Universal import helper for Paper Planner project.

This module can be imported from anywhere in the project to set up proper imports.
It automatically detects the project structure and configures Python paths.

Usage:
    # At the top of any file that needs backend imports:
    import project_imports
    
    # Now you can import backend modules:
    from core.models import Config
    from schedulers.base import BaseScheduler
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict


class ProjectImportManager:
    """Manages imports for the Paper Planner project."""
    
    _instance: Optional['ProjectImportManager'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.project_root: Optional[Path] = None
            self.backend_root: Optional[Path] = None
            self.backend_src: Optional[Path] = None
            self.frontend_root: Optional[Path] = None
            self._setup_paths()
            ProjectImportManager._initialized = True
    
    def _find_project_root(self) -> Optional[Path]:
        """Find the project root by looking for distinctive markers."""
        # Start from the current file's directory
        current = Path(__file__).resolve().parent
        
        # Look for project root indicators
        for path in [current] + list(current.parents):
            # Check for both backend and frontend directories
            if (path / "backend" / "src" / "core").exists() and (path / "frontend" / "app").exists():
                return path
            
            # Check for just backend (if we're in a backend-only context)
            if (path / "src" / "core" / "models.py").exists():
                return path.parent if path.name == "backend" else path
        
        return None
    
    def _setup_paths(self) -> None:
        """Set up all project paths."""
        self.project_root = self._find_project_root()
        if not self.project_root:
            print("Warning: Could not auto-detect project root")
            return
        
        # Determine structure
        if (self.project_root / "backend").exists():
            # Standard structure: project_root/backend/src
            self.backend_root = self.project_root / "backend"
            self.backend_src = self.backend_root / "src"
            self.frontend_root = self.project_root / "frontend"
        else:
            # Direct structure: project_root/src (we're in backend root)
            self.backend_root = self.project_root
            self.backend_src = self.project_root / "src"
            self.frontend_root = self.project_root.parent / "frontend"
        
        # Add to Python path
        if self.backend_src and self.backend_src.exists():
            backend_src_str = str(self.backend_src)
            if backend_src_str not in sys.path:
                sys.path.insert(0, backend_src_str)
                os.environ['PYTHONPATH'] = backend_src_str
    
    def get_paths(self) -> Dict[str, Optional[Path]]:
        """Get all configured paths."""
        return {
            'project_root': self.project_root,
            'backend_root': self.backend_root,
            'backend_src': self.backend_src,
            'frontend_root': self.frontend_root
        }
    
    def is_backend_available(self) -> bool:
        """Check if backend imports are available."""
        try:
            import core.models
            return True
        except ImportError:
            return False
    
    def print_status(self) -> None:
        """Print the current import manager status."""
        paths = self.get_paths()
        print("📁 Project Import Manager Status:")
        for key, path in paths.items():
            status = "✅" if path and path.exists() else "❌"
            print(f"  {status} {key}: {path}")
        
        backend_status = "✅" if self.is_backend_available() else "❌"
        print(f"  {backend_status} Backend imports: {'Available' if self.is_backend_available() else 'Not available'}")


# Initialize the import manager when this module is imported
_manager = ProjectImportManager()

# Export convenience functions
def get_project_root() -> Optional[Path]:
    """Get the project root directory."""
    return _manager.project_root

def get_backend_src() -> Optional[Path]:
    """Get the backend src directory."""
    return _manager.backend_src

def is_backend_available() -> bool:
    """Check if backend imports are working."""
    return _manager.is_backend_available()

def print_import_status() -> None:
    """Print the current import status."""
    _manager.print_status()


# Auto-setup message (only show if running directly)
if __name__ == "__main__":
    print("🚀 Paper Planner Project Import Manager")
    print_import_status()
    
    if is_backend_available():
        print("\n✅ Backend imports are working!")
        print("You can now import backend modules from anywhere in the project.")
    else:
        print("\n❌ Backend imports are not working.")
        print("Check that the backend/src directory exists and contains the core modules.")
else:
    # Silent setup when imported as a module
    pass
