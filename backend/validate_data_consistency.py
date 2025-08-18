#!/usr/bin/env python3
"""
Data consistency validation script.

This script analyzes the data files in both backend/data and backend/tests/common/data
to ensure consistency and identify unused fields that can be deprecated.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import defaultdict

def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_field_usage(data: Any, field_usage: Dict[str, Set[str]]) -> None:
    """Recursively analyze field usage in JSON data."""
    if isinstance(data, dict):
        for key, value in data.items():
            field_usage[key].add(type(value).__name__)
            analyze_field_usage(value, field_usage)
    elif isinstance(data, list):
        for item in data:
            analyze_field_usage(item, field_usage)

def compare_data_structures(backend_data: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compare data structures between backend and test data."""
    comparison = {
        "missing_in_backend": [],
        "missing_in_tests": [],
        "different_values": [],
        "field_count_differences": {}
    }
    
    # Compare field counts
    for data_type in ["conferences", "mods", "papers"]:
        if data_type in backend_data and data_type in test_data:
            backend_count = len(backend_data[data_type]) if backend_data[data_type] else 0
            test_count = len(test_data[data_type]) if test_data[data_type] else 0
            if backend_count != test_count:
                comparison["field_count_differences"][data_type] = {
                    "backend": backend_count,
                    "tests": test_count
                }
    
    # Compare individual fields in papers
    if "papers" in backend_data and "papers" in test_data:
        backend_papers = backend_data["papers"] or []
        test_papers = test_data["papers"] or []
        
        # Check for missing fields
        if backend_papers and test_papers:
            backend_fields = set(backend_papers[0].keys())
            test_fields = set(test_papers[0].keys())
            
            comparison["missing_in_backend"] = list(test_fields - backend_fields)
            comparison["missing_in_tests"] = list(backend_fields - test_fields)
    
    return comparison

def validate_required_fields(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate that required fields are present and have valid values."""
    validation_results = {
        "errors": [],
        "warnings": []
    }
    
    # Check papers
    if "papers" in data and data["papers"]:
        for i, paper in enumerate(data["papers"]):
            # Required fields
            if not paper.get("id"):
                validation_results["errors"].append(f"Paper {i}: Missing required field 'id'")
            if not paper.get("title"):
                validation_results["errors"].append(f"Paper {i}: Missing required field 'title'")
            
            # Validate field types
            if "draft_window_months" in paper and not isinstance(paper["draft_window_months"], int):
                validation_results["warnings"].append(f"Paper {i}: 'draft_window_months' should be int, got {type(paper['draft_window_months'])}")
            
            if "lead_time_from_parents" in paper and not isinstance(paper["lead_time_from_parents"], int):
                validation_results["warnings"].append(f"Paper {i}: 'lead_time_from_parents' should be int, got {type(paper['lead_time_from_parents'])}")
            
            if "penalty_cost_per_month" in paper and not isinstance(paper["penalty_cost_per_month"], (int, float)):
                validation_results["warnings"].append(f"Paper {i}: 'penalty_cost_per_month' should be numeric, got {type(paper['penalty_cost_per_month'])}")
    
    # Check conferences
    if "conferences" in data and data["conferences"]:
        for i, conf in enumerate(data["conferences"]):
            if not conf.get("name"):
                validation_results["errors"].append(f"Conference {i}: Missing required field 'name'")
            
            if "conference_type" in conf and conf["conference_type"] not in ["MEDICAL", "ENGINEERING"]:
                validation_results["warnings"].append(f"Conference {i}: 'conference_type' should be 'MEDICAL' or 'ENGINEERING', got {conf['conference_type']}")
    
    return validation_results

def identify_unused_fields(field_usage: Dict[str, Set[str]], required_fields: Set[str]) -> List[str]:
    """Identify fields that appear to be unused based on codebase analysis."""
    # Fields that are definitely used (based on code analysis)
    definitely_used = {
        "id", "title", "kind", "author", "conference_id", "depends_on",
        "draft_window_months", "lead_time_from_parents", "candidate_conferences",
        "submission_workflow", "engineering", "engineering_ready_date",
        "free_slack_months", "penalty_cost_per_month", "name", "conference_type",
        "recurrence", "abstract_deadline", "full_paper_deadline"
    }
    
    # Fields that might be unused
    potentially_unused = []
    for field in field_usage:
        if field not in definitely_used and field not in required_fields:
            potentially_unused.append(field)
    
    return potentially_unused

def main():
    """Main validation function."""
    print("🔍 Data Consistency Validation")
    print("=" * 50)
    
    # Paths
    backend_dir = Path("data")
    test_dir = Path("tests/common/data")
    
    if not backend_dir.exists():
        print(f"❌ Backend data directory not found: {backend_dir}")
        sys.exit(1)
    
    if not test_dir.exists():
        print(f"❌ Test data directory not found: {test_dir}")
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
    
    # Analyze field usage
    print("\n🔍 Analyzing field usage...")
    field_usage = defaultdict(set)
    
    for data in backend_data.values():
        analyze_field_usage(data, field_usage)
    
    for data in test_data.values():
        analyze_field_usage(data, field_usage)
    
    print(f"  📊 Found {len(field_usage)} unique fields")
    
    # Compare structures
    print("\n🔄 Comparing data structures...")
    comparison = compare_data_structures(backend_data, test_data)
    
    if comparison["field_count_differences"]:
        print("  ⚠️  Data count differences:")
        for data_type, counts in comparison["field_count_differences"].items():
            print(f"    {data_type}: backend={counts['backend']}, tests={counts['tests']}")
    
    if comparison["missing_in_backend"]:
        print("  ⚠️  Fields missing in backend data:")
        for field in comparison["missing_in_backend"]:
            print(f"    - {field}")
    
    if comparison["missing_in_tests"]:
        print("  ⚠️  Fields missing in test data:")
        for field in comparison["missing_in_tests"]:
            print(f"    - {field}")
    
    # Validate required fields
    print("\n✅ Validating required fields...")
    
    backend_validation = validate_required_fields(backend_data)
    test_validation = validate_required_fields(test_data)
    
    if backend_validation["errors"]:
        print("  ❌ Backend data validation errors:")
        for error in backend_validation["errors"]:
            print(f"    - {error}")
    
    if test_validation["errors"]:
        print("  ❌ Test data validation errors:")
        for error in test_validation["errors"]:
            print(f"    - {error}")
    
    if backend_validation["warnings"]:
        print("  ⚠️  Backend data validation warnings:")
        for warning in backend_validation["warnings"]:
            print(f"    - {warning}")
    
    if test_validation["warnings"]:
        print("  ⚠️  Test data validation warnings:")
        for warning in test_validation["warnings"]:
            print(f"    - {warning}")
    
    # Identify potentially unused fields
    print("\n🗑️  Identifying potentially unused fields...")
    required_fields = set()
    for validation in [backend_validation, test_validation]:
        for error in validation["errors"]:
            # Extract field name from error message
            if "Missing required field" in error:
                field = error.split("'")[1]
                required_fields.add(field)
    
    potentially_unused = identify_unused_fields(field_usage, required_fields)
    
    if potentially_unused:
        print("  🔍 Potentially unused fields (consider deprecating):")
        for field in sorted(potentially_unused):
            print(f"    - {field}")
    else:
        print("  ✅ All fields appear to be used")
    
    # Summary
    print("\n📋 Summary")
    print("=" * 50)
    
    total_errors = len(backend_validation["errors"]) + len(test_validation["errors"])
    total_warnings = len(backend_validation["warnings"]) + len(test_validation["warnings"])
    
    if total_errors == 0 and total_warnings == 0 and not comparison["field_count_differences"]:
        print("🎉 All data files are consistent and valid!")
    else:
        print(f"⚠️  Found {total_errors} errors, {total_warnings} warnings")
        if comparison["field_count_differences"]:
            print("   Data count differences detected")
    
    if potentially_unused:
        print(f"🔍 {len(potentially_unused)} potentially unused fields identified")
    
    print("\n💡 Recommendations:")
    if comparison["field_count_differences"]:
        print("  - Consider aligning data volumes between backend and tests")
    if comparison["missing_in_backend"] or comparison["missing_in_tests"]:
        print("  - Align field sets between backend and test data")
    if potentially_unused:
        print("  - Review and potentially deprecate unused fields")
    
    return total_errors == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
