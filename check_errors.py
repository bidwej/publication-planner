#!/usr/bin/env python3
"""Check for errors and verify dates."""

import json

def main():
    print('=== CHECKING FOR ERRORS ===')
    try:
        from src.core.config import load_config
        config = load_config('config.json')
        print(f'✅ Config loads successfully: {len(config.submissions)} submissions')
    except Exception as e:
        print(f'❌ Config loading error: {e}')
        return

    print('\n=== CHECKING DATES ===')
    # Check a few mod dates to make sure they weren't corrupted
    with open('data/mods.json') as f:
        mods = json.load(f)

    print('Sample mod dates:')
    for mod in mods[:5]:
        eng_date = mod.get('engineering_ready_date', 'None')
        print(f'  {mod["id"]}: {eng_date}')

    print('\n=== CHECKING TEST DATA ===')
    try:
        with open('tests/common/data/mods.json') as f:
            test_mods = json.load(f)
        print(f'✅ Test mods file exists: {len(test_mods)} mods')
        
        with open('tests/common/data/papers.json') as f:
            test_papers = json.load(f)
        print(f'✅ Test papers file exists: {len(test_papers)} papers')
    except FileNotFoundError as e:
        print(f'❌ Test data file missing: {e}')
    except Exception as e:
        print(f'❌ Test data error: {e}')

if __name__ == "__main__":
    main()
