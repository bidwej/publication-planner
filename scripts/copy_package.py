import os
import shutil
import importlib.util
from typing import Optional, Set, List
import argparse
from importlib.metadata import distribution, PackageNotFoundError
import re

def _package_path(name: str) -> Optional[str]:
    spec = importlib.util.find_spec(name)
    return spec.submodule_search_locations[0] if spec and spec.submodule_search_locations else None

def _direct_deps(name: str) -> List[str]:
    try:
        dist = distribution(name)
        requires = dist.requires or []
        deps = []
        for r in requires:
            match = re.match(r"^\s*([A-Za-z0-9_.\-]+)", r)
            if match:
                deps.append(match.group(1))
        return deps
    except PackageNotFoundError:
        return []

def _collect_all_deps(root: str) -> List[str]:
    seen: Set[str] = set()
    queue: List[str] = [root]
    order: List[str] = []

    while queue:
        pkg = queue.pop(0)
        if pkg in seen:
            continue
        seen.add(pkg)
        order.append(pkg)
        queue.extend(_direct_deps(pkg))
    return order

def _copy_one(name: str, dest: str) -> None:
    src = _package_path(name)
    if not src:
        print(f"ℹ️  Skipping {name}: not installed in this environment.")
        return
    dst = os.path.join(dest, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    print(f"→ Copying {name}")
    shutil.copytree(src, dst, dirs_exist_ok=True)

def copy_with_deps(root_pkg: str, dest_dir: str = "./third_party") -> None:
    os.makedirs(dest_dir, exist_ok=True)
    all_pkgs = _collect_all_deps(root_pkg)
    if not all_pkgs:
        print(f"⚠️ No packages found for {root_pkg}")
        return
    for pkg in all_pkgs:
        _copy_one(pkg, dest_dir)

def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Copy a Python package and all its dependencies into a local folder."
    )
    parser.add_argument(
        "package",
        nargs="?",
        default="pulp",
        help="Root package name to copy (default: pulp)"
    )
    parser.add_argument(
        "--dest",
        default="./third_party",
        help="Destination directory (default: ./third_party)"
    )
    args = parser.parse_args()
    copy_with_deps(args.package, args.dest)

if __name__ == "__main__":
    cli()
