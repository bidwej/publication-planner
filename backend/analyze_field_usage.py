#!/usr/bin/env python3
"""
Analyze actual field usage in the codebase to identify truly unused fields.

This script searches through the source code to see which JSON fields are actually
referenced and used, providing a more accurate assessment of what can be deprecated.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

def search_code_for_field_usage(field_name: str, source_dir: Path) -> List[str]:
    """Search for actual usage of a field in the source code."""
    usage_locations = []
    
    # Search in Python files
    for py_file in source_dir.rglob("*.py"):
        if "test" in py_file.name.lower():
            continue  # Skip test files for this analysis
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for various patterns of field usage
                patterns = [
                    rf'\.{field_name}\b',  # obj.field_name
                    rf'\[["\']{field_name}["\']\]',  # obj["field_name"] or obj['field_name']
                    rf'get\(["\']{field_name}["\']',  # obj.get("field_name")
                    rf'["\']{field_name}["\']:',  # "field_name": value in dict
                    rf'field_name\s*=',  # field_name = value
                    rf'field_name\s*:',  # field_name: type annotation
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        usage_locations.append(f"{py_file.relative_to(source_dir)}:{line_num}")
                        break  # Only report first match per file
                        
        except Exception as e:
            print(f"Warning: Could not read {py_file}: {e}")
    
    return usage_locations

def analyze_json_structure(data: Any, path: str = "") -> Dict[str, Any]:
    """Analyze JSON structure and extract field information."""
    structure = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            structure[current_path] = {
                "type": type(value).__name__,
                "value": str(value)[:100] if value is not None else None,
                "is_list": isinstance(value, list),
                "list_length": len(value) if isinstance(value, list) else None
            }
            if isinstance(value, (dict, list)):
                structure[current_path]["nested"] = analyze_json_structure(value, current_path)
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            # Analyze first item as representative
            structure = analyze_json_structure(data[0], path)
    
    return structure

def compare_field_usage(backend_data: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compare field usage between backend and test data."""
    comparison = {
        "backend_only": set(),
        "test_only": set(),
        "common": set(),
        "different_values": {},
        "structure_differences": {}
    }
    
    # Analyze structures
    backend_structure = {}
    test_structure = {}
    
    for data_type, data in backend_data.items():
        if data:
            backend_structure[data_type] = analyze_json_structure(data)
    
    for data_type, data in test_data.items():
        if data:
            test_structure[data_type] = analyze_json_structure(data)
    
    # Compare fields
    for data_type in set(backend_structure.keys()) | set(test_structure.keys()):
        if data_type in backend_structure and data_type in test_structure:
            backend_fields = set(backend_structure[data_type].keys())
            test_fields = set(test_structure[data_type].keys())
            
            comparison["common"].update(backend_fields & test_fields)
            comparison["backend_only"].update(backend_fields - test_fields)
            comparison["test_only"].update(test_fields - backend_fields)
            
            # Check for value differences in common fields
            for field in comparison["common"]:
                if (field in backend_structure[data_type] and 
                    field in test_structure[data_type]):
                    backend_info = backend_structure[data_type][field]
                    test_info = test_structure[data_type][field]
                    
                    if (backend_info["type"] != test_info["type"] or
                        backend_info["list_length"] != test_info["list_length"]):
                        comparison["different_values"][field] = {
                            "backend": backend_info,
                            "test": test_info
                        }
    
    return comparison

def main():
    """Main analysis function."""
    print("🔍 Field Usage Analysis")
    print("=" * 50)
    
    # Paths
    backend_dir = Path("data")
    test_dir = Path("tests/common/data")
    source_dir = Path("src")
    
    if not backend_dir.exists():
        print(f"❌ Backend data directory not found: {backend_dir}")
        sys.exit(1)
    
    if not test_dir.exists():
        print(f"❌ Test data directory not found: {test_dir}")
        sys.exit(1)
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        sys.exit(1)
    
    # Load data files
    print("\n📁 Loading data files...")
    
    backend_data = {}
    test_data = {}
    
    # Load backend data
    for data_file in ["config.json", "conferences.json", "mod_papers.json", "ed_papers.json"]:
        file_path = backend_dir / data_file
        if file_path.exists():
            data = load_json_file(file_path)
            if data is not None:
                backend_data[data_file.replace('.json', '')] = data
                print(f"  ✅ Loaded backend/{data_file}")
    
    # Load test data
    for data_file in ["config.json", "conferences.json", "mod_papers.json", "ed_papers.json"]:
        file_path = test_dir / data_file
        if file_path.exists():
            data = load_json_file(file_path)
            if data is not None:
                test_data[data_file.replace('.json', '')] = data
                print(f"  ✅ Loaded tests/{data_file}")
    
    # Compare structures
    print("\n🔄 Comparing data structures...")
    comparison = compare_field_usage(backend_data, test_data)
    
    print(f"  📊 Common fields: {len(comparison['common'])}")
    print(f"  📊 Backend-only fields: {len(comparison['backend_only'])}")
    print(f"  📊 Test-only fields: {len(comparison['test_only'])}")
    
    if comparison["backend_only"]:
        print("\n  🔍 Backend-only fields:")
        for field in sorted(comparison["backend_only"]):
            print(f"    - {field}")
    
    if comparison["test_only"]:
        print("\n  🔍 Test-only fields:")
        for field in sorted(comparison["test_only"]):
            print(f"    - {field}")
    
    # Analyze field usage in source code
    print("\n🔍 Analyzing field usage in source code...")
    
    # Get all unique field names
    all_fields = set()
    for data in backend_data.values():
        if isinstance(data, list) and data:
            all_fields.update(data[0].keys())
        elif isinstance(data, dict):
            all_fields.update(data.keys())
    
    for data in test_data.values():
        if isinstance(data, list) and data:
            all_fields.update(data[0].keys())
        elif isinstance(data, dict):
            all_fields.update(data.keys())
    
    print(f"  📊 Total unique fields found: {len(all_fields)}")
    
    # Check usage of each field
    field_usage = {}
    for field in sorted(all_fields):
        usage = search_code_for_field_usage(field, source_dir)
        field_usage[field] = usage
    
    # Categorize fields
    used_fields = {field: usage for field, usage in field_usage.items() if usage}
    unused_fields = {field: usage for field, usage in field_usage.items() if not usage}
    
    print(f"\n  ✅ Used fields: {len(used_fields)}")
    print(f"  ❌ Unused fields: {len(unused_fields)}")
    
    if unused_fields:
        print("\n  🔍 Potentially unused fields (consider deprecating):")
        for field in sorted(unused_fields.keys()):
            print(f"    - {field}")
    
    # Summary and recommendations
    print("\n📋 Summary")
    print("=" * 50)
    
    print(f"📊 Data consistency:")
    print(f"  - Common fields: {len(comparison['common'])}")
    print(f"  - Backend-only: {len(comparison['backend_only'])}")
    print(f"  - Test-only: {len(comparison['test_only'])}")
    
    print(f"\n📊 Field usage:")
    print(f"  - Used in code: {len(used_fields)}")
    print(f"  - Unused: {len(unused_fields)}")
    
    print("\n💡 Recommendations:")
    
    if comparison["backend_only"] or comparison["test_only"]:
        print("  - Align field sets between backend and test data")
        print("  - Consider which fields should be common vs. environment-specific")
    
    if unused_fields:
        print("  - Review and potentially deprecate unused fields")
        print("  - Ensure deprecated fields are removed from both data sets")
    
    if len(comparison["common"]) < len(all_fields) * 0.8:
        print("  - Consider standardizing more fields between environments")
    
    return len(unused_fields) == 0

def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
