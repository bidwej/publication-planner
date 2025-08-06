#!/usr/bin/env python3
"""
Copy a package to a new location with optional filtering.
"""

import argparse
import shutil
from pathlib import Path
from typing import List, Callable, Optional

def is_ignored(path: Path, ignore_patterns: List[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    path_str = str(path)
    return any(pattern in path_str for pattern in ignore_patterns)

def copy_package(
    source: str,
    destination: str,
    ignore_patterns: List[str] = None,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> None:
    """
    Copy a package to a new location with optional filtering.
    
    Args:
        source: Source directory path
        destination: Destination directory path
        ignore_patterns: List of patterns to ignore
        filter_func: Optional function to filter files
    """
    if ignore_patterns is None:
        ignore_patterns = []
    
    src_path = Path(source)
    dst_path = Path(destination)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")
    
    # Create destination directory
    dst_path.mkdir(parents=True, exist_ok=True)
    
    # Copy files recursively
    for item in src_path.rglob("*"):
        if item.is_file():
            # Check if file should be ignored
            if is_ignored(item, ignore_patterns):
                continue
            
            # Apply custom filter if provided
            if filter_func and not filter_func(item):
                continue
            
            # Calculate relative path
            relative_path = item.relative_to(src_path)
            dst_file = dst_path / relative_path
            
            # Create parent directories
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(item, dst_file)
            print(f"Copied: {relative_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Copy a package to a new location")
    parser.add_argument("source", help="Source directory")
    parser.add_argument("dest", help="Destination directory")
    parser.add_argument("--ignore", nargs="*", default=[], help="Patterns to ignore")
    parser.add_argument("--root-package", default="pulp", help="Root package name to copy (default: pulp)")
    
    args = parser.parse_args()
    
    try:
        copy_package(args.source, args.dest, args.ignore)
        print(f"Successfully copied {args.source} to {args.dest}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()