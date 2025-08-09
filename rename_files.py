#!/usr/bin/env python3
"""Rename files to be more descriptive: mods.json -> mod_papers.json, papers.json -> ed_papers.json"""

import json
import shutil
from pathlib import Path

def main():
    print("=== RENAMING FILES FOR CLARITY ===")
    
    # Main data directory
    data_dir = Path("data")
    test_data_dir = Path("tests/common/data")
    
    # Rename mappings
    renames = {
        "mods.json": "mod_papers.json",     # PCCP research papers
        "papers.json": "ed_papers.json"    # Ed's suggested papers
    }
    
    # Rename in main data directory
    for old_name, new_name in renames.items():
        old_file = data_dir / old_name
        new_file = data_dir / new_name
        
        if old_file.exists():
            shutil.move(str(old_file), str(new_file))
            print(f"✅ Renamed {old_name} → {new_name}")
        else:
            print(f"❌ {old_name} not found")
    
    # Rename in test data directory  
    test_data_dir.mkdir(parents=True, exist_ok=True)
    for old_name, new_name in renames.items():
        old_file = test_data_dir / old_name
        new_file = test_data_dir / new_name
        
        if old_file.exists():
            shutil.move(str(old_file), str(new_file))
            print(f"✅ Test: Renamed {old_name} → {new_name}")
        else:
            print(f"❌ Test: {old_name} not found")
    
    print("\n=== FILE MEANINGS ===")
    print("📄 mod_papers.json  - Papers from PCCP research team (mods)")
    print("📄 ed_papers.json   - Papers suggested by Ed")
    print("📄 conferences.json - Conference information")
    
    print("\n=== NEXT STEPS ===")
    print("1. Update config.json to reference new file names")
    print("2. Update any code references")
    print("3. Both file types now clearly represent 'papers' with different sources")

if __name__ == "__main__":
    main()
