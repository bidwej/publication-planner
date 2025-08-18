"""
Data consistency checker for ensuring backend and test data alignment.

This module provides functions to validate that data files are consistent
between environments and follow the expected schema.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

def validate_data_consistency(backend_dir: Path, test_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate consistency between backend and test data.
    
    Returns:
        Tuple of (is_consistent, list_of_issues)
    """
    issues = []
    
    # Check that both environments have the same data files
    backend_files = set(f.name for f in backend_dir.glob("*.json"))
    test_files = set(f.name for f in test_dir.glob("*.json"))
    
    missing_in_backend = test_files - backend_files
    missing_in_tests = backend_files - test_files
    
    if missing_in_backend:
        issues.append(f"Files missing in backend: {missing_in_backend}")
    
    if missing_in_tests:
        issues.append(f"Files missing in tests: {missing_in_tests}")
    
    # Check common files for schema consistency
    common_files = backend_files & test_files
    for filename in common_files:
        backend_path = backend_dir / filename
        test_path = test_dir / filename
        
        try:
            with open(backend_path, 'r') as f:
                backend_data = json.load(f)
            with open(test_path, 'r') as f:
                test_data = json.load(f)
            
            # Compare structure (not values, as they may differ intentionally)
            if isinstance(backend_data, list) and isinstance(test_data, list):
                if backend_data and test_data:
                    backend_keys = set(backend_data[0].keys())
                    test_keys = set(test_data[0].keys())
                    
                    missing_in_backend = test_keys - backend_keys
                    missing_in_tests = backend_keys - test_keys
                    
                    if missing_in_backend:
                        issues.append(f"{filename}: Fields missing in backend: {missing_in_backend}")
                    if missing_in_tests:
                        issues.append(f"{filename}: Fields missing in tests: {missing_in_tests}")
            
        except Exception as e:
            issues.append(f"Error processing {filename}: {e}")
    
    return len(issues) == 0, issues

def validate_schema_compliance(data_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate that data files comply with the expected schema.
    
    Returns:
        Tuple of (is_compliant, list_of_issues)
    """
    issues = []
    
    # Load schema
    schema_file = Path("data_validation_schema.json")
    if not schema_file.exists():
        issues.append("Schema file not found")
        return False, issues
    
    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    except Exception as e:
        issues.append(f"Error loading schema: {e}")
        return False, issues
    
    # Validate each data type
    for data_type, type_schema in schema.items():
        data_file = data_dir / f"{data_type}.json"
        if not data_file.exists():
            continue
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list) and data:
                # Check required fields
                for item in data:
                    for required_field in type_schema.get("required", []):
                        if required_field not in item:
                            issues.append(f"{data_type}: Missing required field '{required_field}' in item {item.get('id', 'unknown')}")
                
                # Check for deprecated fields
                for item in data:
                    for deprecated_field in type_schema.get("deprecated", []):
                        if deprecated_field in item:
                            issues.append(f"{data_type}: Deprecated field '{deprecated_field}' found in item {item.get('id', 'unknown')}")
        
        except Exception as e:
            issues.append(f"Error validating {data_type}: {e}")
    
    return len(issues) == 0, issues

if __name__ == "__main__":
    # Example usage
    backend_dir = Path("data")
    test_dir = Path("tests/common/data")
    
    print("Checking data consistency...")
    is_consistent, consistency_issues = validate_data_consistency(backend_dir, test_dir)
    
    if not is_consistent:
        print("❌ Data consistency issues found:")
        for issue in consistency_issues:
            print(f"  - {issue}")
    else:
        print("✅ Data is consistent between environments")
    
    print("\nChecking schema compliance...")
    is_compliant, schema_issues = validate_schema_compliance(backend_dir)
    
    if not is_compliant:
        print("❌ Schema compliance issues found:")
        for issue in schema_issues:
            print(f"  - {issue}")
    else:
        print("✅ Data complies with schema")
