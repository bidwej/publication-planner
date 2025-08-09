#!/usr/bin/env python3
"""
Simple test script to generate timeline screenshots and check for issues.
"""

import asyncio
import time
from pathlib import Path
from tests.common.headless_browser import capture_timeline_screenshots

def main():
    """Generate multiple timeline screenshots to test for issues."""
    print("🔍 Testing timeline generation...")
    
    # Generate multiple screenshots to check for consistency
    for i in range(3):
        print(f"\n📸 Generating timeline screenshot #{i+1}...")
        
        try:
            result = asyncio.run(capture_timeline_screenshots())
            if result:
                print(f"✅ Screenshot #{i+1} generated successfully")
            else:
                print(f"❌ Screenshot #{i+1} failed")
        except Exception as e:
            print(f"❌ Error generating screenshot #{i+1}: {e}")
        
        # Wait a bit between screenshots
        time.sleep(2)
    
    # Check if PNG files were created
    png_files = list(Path(".").glob("web_timeline*.png"))
    print(f"\n📁 Found {len(png_files)} timeline PNG files:")
    for png_file in png_files:
        print(f"  - {png_file.name} ({png_file.stat().st_size} bytes)")
    
    print("\n🎯 Timeline test completed!")

if __name__ == "__main__":
    main()
