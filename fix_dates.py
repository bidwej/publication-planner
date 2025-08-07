#!/usr/bin/env python3
"""Fix dates in test file."""

import re

# Read the test file
with open('tests/src/schedulers/test_greedy.py', 'r') as f:
    content = f.read()

# Replace all 2024 dates with 2025 dates
content = re.sub(r'date\(2024,', 'date(2025,', content)

# Write back to file
with open('tests/src/schedulers/test_greedy.py', 'w') as f:
    f.write(content)

print("Fixed all 2024 dates to 2025 dates in test_greedy.py")
