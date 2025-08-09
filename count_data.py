#!/usr/bin/env python3
"""
Count data files to understand the scale
"""

import json
from pathlib import Path

def main():
    # Count papers
    papers_path = Path('data/papers.json')
    if papers_path.exists():
        with open(papers_path) as f:
            papers = json.load(f)
        print(f'Papers: {len(papers)}')
        for p in papers[:5]:  # Show first 5
            print(f'  - {p["id"]}: {p["title"]}')
        if len(papers) > 5:
            print(f'  ... and {len(papers) - 5} more')

    # Count conferences
    conf_path = Path('data/conferences.json')
    if conf_path.exists():
        with open(conf_path) as f:
            conferences = json.load(f)
        print(f'Conferences: {len(conferences)}')
        for c in conferences[:5]:  # Show first 5
            print(f'  - {c["name"]}')
        if len(conferences) > 5:
            print(f'  ... and {len(conferences) - 5} more')

    # Count mods
    mods_path = Path('data/mods.json')
    if mods_path.exists():
        with open(mods_path) as f:
            mods = json.load(f)
        print(f'Mods: {len(mods)}')

    if papers_path.exists() and conf_path.exists():
        print(f'Potential combinations: {len(papers) * len(conferences)}')

if __name__ == "__main__":
    main()
