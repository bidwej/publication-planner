"""
Test the unified web charts runner script functionality.
"""

import sys
import pytest
import subprocess
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

def test_web_charts_runner_import():
    """Test that the web charts runner can be imported."""
    try:
        from run_web_charts import (
            run_dashboard, 
            run_timeline, 
            capture_dashboard_screenshots, 
            capture_timeline_screenshot, 
            main
        )
        print("✅ Web charts runner imports successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import web charts runner: {e}")

def test_web_charts_runner_help():
    """Test that the web charts runner shows help."""
    result = subprocess.run(
        ["python", "run_web_charts.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    assert result.returncode == 0, "Help command should succeed"
    assert "Paper Planner Web Charts Runner" in result.stdout
    assert "--mode" in result.stdout
    assert "--capture" in result.stdout
    assert "dashboard" in result.stdout
    assert "timeline" in result.stdout

def test_web_charts_runner_default_mode():
    """Test that the web charts runner defaults to dashboard mode."""
    result = subprocess.run(
        ["python", "run_web_charts.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    assert "default:" in result.stdout
    assert "dashboard" in result.stdout

@pytest.mark.asyncio
async def test_capture_dashboard_screenshots():
    """Test the capture dashboard screenshots function."""
    try:
        from run_web_charts import capture_dashboard_screenshots
        
        # Mock the headless browser module
        with patch('tests.common.headless_browser.capture_all_scheduler_options') as mock_capture:
            mock_capture.return_value = {
                'greedy': True,
                'optimal': True,
                'heuristic': False,
                'random': True
            }
            
            # Test the function
            await capture_dashboard_screenshots()
            
            # Verify the mock was called
            mock_capture.assert_called_once()
            
            print("✅ Dashboard screenshot capture function works")
            
    except Exception as e:
        pytest.fail(f"Dashboard screenshot capture test failed: {e}")

@pytest.mark.asyncio
async def test_capture_timeline_screenshot():
    """Test the capture timeline screenshot function."""
    try:
        from run_web_charts import capture_timeline_screenshot
        
        # Mock the headless browser module
        with patch('tests.common.headless_browser.capture_timeline_screenshots') as mock_capture:
            mock_capture.return_value = True
            
            # Test the function
            await capture_timeline_screenshot()
            
            # Verify the mock was called
            mock_capture.assert_called_once()
            
            print("✅ Timeline screenshot capture function works")
            
    except Exception as e:
        pytest.fail(f"Timeline screenshot capture test failed: {e}")

def test_web_charts_runner_main_dashboard_normal():
    """Test the main function in dashboard normal mode."""
    try:
        from run_web_charts import main
        
        # Mock argparse to simulate dashboard normal mode
        with patch('sys.argv', ['run_web_charts.py', '--mode', 'dashboard']):
            with patch('run_web_charts.run_dashboard') as mock_run:
                main()
                mock_run.assert_called_once()
                
        print("✅ Web charts runner main function works in dashboard normal mode")
        
    except Exception as e:
        pytest.fail(f"Web charts runner dashboard normal test failed: {e}")

def test_web_charts_runner_main_timeline_normal():
    """Test the main function in timeline normal mode."""
    try:
        from run_web_charts import main
        
        # Mock argparse to simulate timeline normal mode
        with patch('sys.argv', ['run_web_charts.py', '--mode', 'timeline']):
            with patch('run_web_charts.run_timeline') as mock_run:
                main()
                mock_run.assert_called_once()
                
        print("✅ Web charts runner main function works in timeline normal mode")
        
    except Exception as e:
        pytest.fail(f"Web charts runner timeline normal test failed: {e}")

def test_web_charts_runner_main_dashboard_capture():
    """Test the main function in dashboard capture mode."""
    try:
        from run_web_charts import main
        
        # Mock argparse to simulate dashboard capture mode
        with patch('sys.argv', ['run_web_charts.py', '--mode', 'dashboard', '--capture']):
            with patch('run_web_charts.capture_dashboard_screenshots') as mock_capture:
                with patch('asyncio.run') as mock_asyncio:
                    main()
                    mock_capture.assert_called_once()
                    mock_asyncio.assert_called_once()
                    
        print("✅ Web charts runner main function works in dashboard capture mode")
        
    except Exception as e:
        pytest.fail(f"Web charts runner dashboard capture test failed: {e}")

def test_web_charts_runner_main_timeline_capture():
    """Test the main function in timeline capture mode."""
    try:
        from run_web_charts import main
        
        # Mock argparse to simulate timeline capture mode
        with patch('sys.argv', ['run_web_charts.py', '--mode', 'timeline', '--capture']):
            with patch('run_web_charts.capture_timeline_screenshot') as mock_capture:
                with patch('asyncio.run') as mock_asyncio:
                    main()
                    mock_capture.assert_called_once()
                    mock_asyncio.assert_called_once()
                    
        print("✅ Web charts runner main function works in timeline capture mode")
        
    except Exception as e:
        pytest.fail(f"Web charts runner timeline capture test failed: {e}")

def test_web_charts_runner_logging():
    """Test that the web charts runner has proper logging setup."""
    try:
        from run_web_charts import logger
        
        # Test that logger is configured
        assert logger is not None, "Logger should be configured"
        assert logger.level <= 20, "Logger should be at INFO level or lower"
        
        print("✅ Web charts runner logging is properly configured")
        
    except Exception as e:
        pytest.fail(f"Web charts runner logging test failed: {e}")

def test_web_charts_runner_default_behavior():
    """Test that the web charts runner defaults to dashboard mode when no mode specified."""
    try:
        from run_web_charts import main
        
        # Mock argparse to simulate no mode specified (should default to dashboard)
        with patch('sys.argv', ['run_web_charts.py']):
            with patch('run_web_charts.run_dashboard') as mock_run:
                main()
                mock_run.assert_called_once()
                
        print("✅ Web charts runner defaults to dashboard mode")
        
    except Exception as e:
        pytest.fail(f"Web charts runner default behavior test failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
