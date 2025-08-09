#!/usr/bin/env python3
"""
Concatenate source files into a single file.
"""

import argparse
from pathlib import Path
from typing import List

def is_ignored(path: Path, ignore_patterns: List[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    path_str = str(path)
    return any(pattern in path_str for pattern in ignore_patterns)

def concat_source_files(
    input_folder: str,
    output_file: str,
    ignore_patterns: List[str] = None,
    file_extensions: List[str] = None
) -> None:
    """
    Concatenate source files into a single file.
    
    Args:
        input_folder: Input folder path
        output_file: Output file path
        ignore_patterns: List of patterns to ignore
        file_extensions: List of file extensions to include
    """
    if ignore_patterns is None:
        ignore_patterns = []
    if file_extensions is None:
        file_extensions = [".py"]
    
    input_path = Path(input_folder)
    output_path = Path(output_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect all source files
    source_files = []
    for file_path in input_path.rglob("*"):
        if file_path.is_file():
            # Check file extension
            if file_path.suffix not in file_extensions:
                continue
            
            # Check if file should be ignored
            if is_ignored(file_path, ignore_patterns):
                continue
            
            source_files.append(file_path)
    
    # Sort files for consistent output
    source_files.sort()
    
    # Write concatenated content
    with open(output_path, 'w', encoding='utf-8') as source_file:
        for file_path in source_files:
            relative_path = file_path.relative_to(input_path)
            source_file.write(f"\n{'='*60}\n")
            source_file.write(f"File: {relative_path}\n")
            source_file.write(f"{'='*60}\n\n")
            source_file.write(file_path.read_text(encoding='utf-8'))
            source_file.write("\n\n")
    
    print("Concatenated %s files into %s", len(source_files), output_file)

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Concatenate source files")
    parser.add_argument("input_folder", help="Input folder path")
    parser.add_argument("output_file", help="Output file path")
    parser.add_argument("--ignore", nargs="*", default=[], help="Patterns to ignore")
    parser.add_argument("--extensions", nargs="*", default=[".py"], help="File extensions to include")
    
    args = parser.parse_args()
    
    try:
        concat_source_files(args.input_folder, args.output_file, args.ignore, args.extensions)
        print("Successfully concatenated files from %s to %s", args.input_folder, args.output_file)
    except Exception as e:
        print("Error: %s", e)

if __name__ == "__main__":
    main()