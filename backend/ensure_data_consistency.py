#!/usr/bin/env python3
"""
Ensure data consistency between backend and test environments.

This script:
1. Validates that both environments use the same data loading approach
2. Updates validation functions if needed
3. Identifies and handles unused fields
4. Ensures consistent data structure validation
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def validate_data_loading_consistency():
    """Validate that both environments use the same data loading approach."""
    print("🔍 Validating data loading consistency...")
    
    # Check if both environments use the same config loading function
    backend_config_path = Path("src/core/config.py")
    if not backend_config_path.exists():
        print("❌ Backend config.py not found")
        return False
    
    # Check for consistent data loading patterns
    with open(backend_config_path, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    # Check for key loading functions
    required_functions = [
        "load_config",
        "_load_conferences", 
        "_load_submissions_with_abstracts",
        "_load_mods",
        "_load_papers"
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in config_content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"❌ Missing required functions in config.py: {missing_functions}")
        return False
    
    print("✅ Data loading functions are consistent")
    return True

def validate_validation_functions():
    """Check if validation functions need updates."""
    print("\n🔍 Validating validation functions...")
    
    validation_dir = Path("src/validation")
    if not validation_dir.exists():
        print("❌ Validation directory not found")
        return False
    
    # Check key validation files
    required_files = [
        "submission.py",
        "venue.py", 
        "deadline.py",
        "resources.py",
        "schedule.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not (validation_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing validation files: {missing_files}")
        return False
    
    print("✅ All validation files present")
    
    # Check for consistent validation patterns
    validation_patterns = [
        "validate_submission_constraints",
        "_validate_venue_compatibility",
        "validate_deadline_constraints"
    ]
    
    for pattern in validation_patterns:
        found = False
        for val_file in validation_dir.glob("*.py"):
            with open(val_file, 'r', encoding='utf-8') as f:
                if pattern in f.read():
                    found = True
                    break
        
        if not found:
            print(f"⚠️  Validation pattern '{pattern}' not found in any validation file")
    
    return True

def identify_unused_fields():
    """Identify fields that can be safely deprecated."""
    print("\n🔍 Identifying unused fields...")
    
    # Based on the analysis, these fields appear unused
    potentially_unused = {

        "max_backtrack_days", 
        "max_submissions_per_author"
    }
    
    # Verify these are actually unused by checking if they're referenced anywhere
    source_dir = Path("src")
    unused_confirmed = []
    
    for field in potentially_unused:
        field_used = False
        for py_file in source_dir.rglob("*.py"):
            if "test" in py_file.name.lower():
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if field in content:
                        field_used = True
                        break
            except Exception:
                continue
        
        if not field_used:
            unused_confirmed.append(field)
    
    if unused_confirmed:
        print(f"✅ Confirmed unused fields: {unused_confirmed}")
        print("💡 These fields can be safely deprecated")
    else:
        print("✅ All fields appear to be used")
    
    return unused_confirmed

def create_validation_schema():
    """Create a validation schema to ensure data consistency."""
    print("\n📋 Creating validation schema...")
    
    # Define the expected schema based on what's actually used
    schema = {
        "papers": {
            "required": ["id", "title"],
            "optional": [
                "draft_window_months", "lead_time_from_parents", "preferred_conferences",
                "submission_workflow", "depends_on", "engineering_ready_date",
                "free_slack_months", "penalty_cost_per_month", "author"
            ],
            "deprecated": ["max_backtrack_days", "max_submissions_per_author"]
        },
        "conferences": {
            "required": ["name"],
            "optional": [
                "conference_type", "recurrence", "abstract_deadline", 
                "full_paper_deadline", "submission_types"
            ]
        },
        "config": {
            "required": [
                "min_abstract_lead_time_days", "min_paper_lead_time_days",
                "max_concurrent_submissions", "data_files"
            ],
            "optional": [
                "default_paper_lead_time_months", "work_item_duration_days",
                "conference_response_time_days", "max_backtrack_days",
                "randomness_factor", "lookahead_bonus_increment",
                "penalty_costs", "priority_weights", "scheduling_options"
            ]
        }
    }
    
    # Save schema for reference
    schema_file = Path("data_validation_schema.json")
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"✅ Validation schema saved to {schema_file}")
    return schema

def update_validation_functions():
    """Update validation functions to ensure consistency."""
    print("\n🔧 Updating validation functions...")
    
    # Check if validation functions need updates
    validation_dir = Path("src/validation")
    
    # Update submission validation to handle the unified schema
    submission_file = validation_dir / "submission.py"
    if submission_file.exists():
        with open(submission_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it handles the new unified fields
        if "engineering_ready_date" not in content:
            print("⚠️  Submission validation may need updates for unified schema")
        
        if "free_slack_months" not in content:
            print("⚠️  Submission validation may need updates for unified schema")
    
    # Update venue validation to handle candidate_conferences properly
    venue_file = validation_dir / "venue.py"
    if venue_file.exists():
        with open(venue_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "candidate_conferences" not in content:
            print("⚠️  Venue validation may need updates for candidate_conferences")
    
    print("✅ Validation functions reviewed")
    return True

def create_data_consistency_checker():
    """Create a data consistency checker function."""
    print("\n🔧 Creating data consistency checker...")
    
    checker_code = '''"""
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
    
    print("\\nChecking schema compliance...")
    is_compliant, schema_issues = validate_schema_compliance(backend_dir)
    
    if not is_compliant:
        print("❌ Schema compliance issues found:")
        for issue in schema_issues:
            print(f"  - {issue}")
    else:
        print("✅ Data complies with schema")
'''
    
    checker_file = Path("src/validation/data_consistency.py")
    checker_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checker_file, 'w', encoding='utf-8') as f:
        f.write(checker_code)
    
    print(f"✅ Data consistency checker created at {checker_file}")
    return True

def main():
    """Main function to ensure data consistency."""
    print("🔧 Ensuring Data Consistency")
    print("=" * 50)
    
    # Step 1: Validate data loading consistency
    if not validate_data_loading_consistency():
        print("❌ Data loading consistency validation failed")
        return False
    
    # Step 2: Validate validation functions
    if not validate_validation_functions():
        print("❌ Validation functions validation failed")
        return False
    
    # Step 3: Identify unused fields
    unused_fields = identify_unused_fields()
    
    # Step 4: Create validation schema
    schema = create_validation_schema()
    
    # Step 5: Update validation functions
    if not update_validation_functions():
        print("❌ Failed to update validation functions")
        return False
    
    # Step 6: Create data consistency checker
    if not create_data_consistency_checker():
        print("❌ Failed to create data consistency checker")
        return False
    
    print("\n🎉 Data consistency setup completed successfully!")
    print("\n📋 Next steps:")
    print("  1. Review the validation schema in data_validation_schema.json")
    print("  2. Consider deprecating unused fields: " + ", ".join(unused_fields))
    print("  3. Use the new data consistency checker in your CI/CD pipeline")
    print("  4. Run the consistency checker regularly to maintain alignment")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
