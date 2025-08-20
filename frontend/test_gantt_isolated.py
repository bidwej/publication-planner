"""
Isolated test to find where gantt interface is hanging.
"""

def test_imports():
    """Test each import step by step."""
    print("Testing imports step by step...")
    
    try:
        print("1. Testing basic imports...")
        from dash import html, dcc
        print("   ✅ Basic Dash imports successful")
    except Exception as e:
        print(f"   ❌ Basic Dash imports failed: {e}")
        return False
    
    try:
        print("2. Testing gantt chart import...")
        from app.components.gantt.chart import create_gantt_chart
        print("   ✅ Gantt chart import successful")
    except Exception as e:
        print(f"   ❌ Gantt chart import failed: {e}")
        return False
    
    try:
        print("3. Testing gantt layout import...")
        from app.components.gantt.layout import create_gantt_layout
        print("   ✅ Gantt layout import successful")
    except Exception as e:
        print(f"   ❌ Gantt layout import failed: {e}")
        return False
    
    try:
        print("4. Testing storage import...")
        from app.storage import get_state_manager
        print("   ✅ Storage import successful")
    except Exception as e:
        print(f"   ❌ Storage import failed: {e}")
        return False
    
    try:
        print("5. Testing exporter controls import...")
        from app.components.exporter.controls import create_export_controls
        print("   ✅ Exporter controls import successful")
    except Exception as e:
        print(f"   ❌ Exporter controls import failed: {e}")
        return False
    
    print("✅ All imports successful!")
    return True

def test_chart_creation():
    """Test chart creation."""
    print("\nTesting chart creation...")
    
    try:
        from app.components.gantt.chart import create_gantt_chart
        print("1. Creating gantt chart...")
        chart = create_gantt_chart(use_sample_data=True)
        print("   ✅ Chart created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Chart creation failed: {e}")
        return False

def test_layout_creation():
    """Test layout creation."""
    print("\nTesting layout creation...")
    
    try:
        from app.components.gantt.layout import create_gantt_layout
        print("1. Creating gantt layout...")
        layout = create_gantt_layout()
        print("   ✅ Layout created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Layout creation failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Testing Gantt Interface Step by Step\n")
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed - stopping here")
        exit(1)
    
    # Test chart creation
    if not test_chart_creation():
        print("\n❌ Chart creation failed - stopping here")
        exit(1)
    
    # Test layout creation
    if not test_layout_creation():
        print("\n❌ Layout creation failed - stopping here")
        exit(1)
    
    print("\n🎉 All tests passed! Gantt interface should work.")
