import os
import shutil
import zipfile
import argparse
import datetime
import tempfile
import fnmatch
from pathlib import Path
from typing import Optional, Set

DEFAULT_INPUT: Path = Path("./")
DEFAULT_OUTPUT: Path = Path("./")

# Folders to ignore (directories)
DEFAULT_IGNORE_FOLDERS: Set[str] = {
    ".venv",
    "__pycache__",
    "deprecated",
    ".git",
    "temp*",  # Matches temp, temp1, temp_code, etc.
    ".pytest_cache",
    "build",
    "docs",
    "runs",
    "node_modules",
    "scripts",
    # "tests",
    "cache",
    "data",
}

# Files to ignore (by exact match or extensions)
DEFAULT_IGNORE_FILES: Set[str] = {
    ".DS_Store",  # Mac system file
    "Thumbs.db",  # Windows system file
}


def should_ignore_folder(folder_name: str, ignore_patterns: Set[str]) -> bool:
    """Check if a folder should be ignored based on patterns."""
    return any(fnmatch.fnmatch(folder_name, pattern) for pattern in ignore_patterns)


def should_ignore_file(file_name: str, ignore_files: Set[str]) -> bool:
    """Check if a file should be ignored based on name or extension."""
    return file_name in ignore_files or any(file_name.endswith(ext) for ext in ignore_files)


def create_archive(
    input_path: Optional[Path] = DEFAULT_INPUT,
    output_path: Optional[Path] = DEFAULT_OUTPUT,
    ignore_folders: Optional[Set[str]] = None,
    ignore_files: Optional[Set[str]] = None,
) -> None:
    """Create a ZIP archive of source code with specified exclusions."""
    if ignore_folders is None:
        ignore_folders = DEFAULT_IGNORE_FOLDERS
    if ignore_files is None:
        ignore_files = DEFAULT_IGNORE_FILES

    # Resolve paths
    input_path = input_path.resolve()
    output_path = output_path.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input path '{input_path}' not found")

    # Prepare archive details
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_name = f"{input_path.name}_{timestamp}.zip"
    archive_path = output_path / archive_name

    # Create temporary staging area
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Walk directory tree efficiently
        for root, dirs, files in os.walk(input_path, topdown=True):
            root_path = Path(root)

            # Filter directories in-place to avoid unnecessary traversal
            dirs[:] = [d for d in dirs if not should_ignore_folder(d, ignore_folders)]

            # Copy files while filtering ignored ones
            for file in files:
                if should_ignore_file(file, ignore_files):
                    continue

                src_file = root_path / file
                rel_path = src_file.relative_to(input_path)
                dest_file = temp_path / rel_path

                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)

        # Create zip archive
        output_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    zf.write(file_path, file_path.relative_to(temp_path))

        print(f"Archive created: {archive_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create source code archive")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"Input directory (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"Output directory (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--ignore-folders", nargs="+", default=DEFAULT_IGNORE_FOLDERS, help="Folders to ignore")
    parser.add_argument("--ignore-files", nargs="+", default=DEFAULT_IGNORE_FILES, help="Files to ignore")

    args = parser.parse_args()
    create_archive(args.input, args.output, set(args.ignore_folders), set(args.ignore_files))
