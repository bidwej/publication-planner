#!/usr/bin/env python3
"""
Simple test script for timeline functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.common.headless_browser import capture_timeline_screenshots

async def test_timeline():
    """Test the timeline functionality."""
    print("Testing timeline capture...")
    result = await capture_timeline_screenshots()
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    result = asyncio.run(test_timeline())
    sys.exit(0 if result else 1)
