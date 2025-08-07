"""Tests for headless browser functionality."""

import pytest
import socket
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Add project root to path for imports
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['PYTHONPATH'] = project_root + os.pathsep + os.environ.get('PYTHONPATH', '')

from tests.common.headless_browser import (
    validate_script_path,
    validate_port,
    validate_url,
    check_port_availability,
    validate_network_connectivity,
    validate_dependencies,
    validate_output_directory,
    validate_configuration,
    ConfigurationError,
    is_server_running,
    start_web_server,
    capture_web_page_screenshot,
    capture_all_scheduler_options,
    capture_timeline_screenshots,
    HeadlessBrowserError,
    ServerStartupError,
    ScreenshotCaptureError
)


class TestValidationFunctions:
    """Test validation functions for configuration and dependencies."""
    
    def test_validate_script_path_valid(self, temp_dir: Path) -> None:
        """Test validating a valid script path."""
        script_path = temp_dir / "test_script.py"
        script_path.write_text("print('test')")
        
        result = validate_script_path(str(script_path))
        assert result is True
    
    def test_validate_script_path_nonexistent(self) -> None:
        """Test validating a non-existent script path."""
        with pytest.raises(ConfigurationError, match="Script not found"):
            validate_script_path("nonexistent_script.py")
    
    def test_validate_port_valid(self) -> None:
        """Test validating valid port numbers."""
        assert validate_port(8080) is True
        assert validate_port(1) is True
        assert validate_port(65535) is True
    
    def test_validate_port_invalid_type(self) -> None:
        """Test validating port with invalid type."""
        with pytest.raises(ConfigurationError, match="Port must be an integer"):
            validate_port("8080")  # type: ignore
    
    def test_validate_url_valid(self) -> None:
        """Test validating valid URLs."""
        assert validate_url("http://localhost:8080") is True
        assert validate_url("https://example.com") is True
    
    def test_validate_url_invalid_format(self) -> None:
        """Test validating URL with invalid format."""
        with pytest.raises(ConfigurationError, match="URL must start with http:// or https://"):
            validate_url("not-a-url")
    
    def test_check_port_availability(self) -> None:
        """Test checking port availability."""
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        assert check_port_availability(available_port) is True
    
    @patch('requests.get')
    def test_validate_network_connectivity_success(self, mock_get: Mock) -> None:
        """Test network connectivity validation with successful connection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = validate_network_connectivity("http://example.com")
        assert result is True
    
    def test_validate_dependencies_success(self) -> None:
        """Test dependency validation when all dependencies are available."""
        result = validate_dependencies()
        assert result is True
    
    def test_validate_output_directory_success(self, temp_dir: Path) -> None:
        """Test output directory validation with valid directory."""
        output_dir = temp_dir / "output"
        
        result = validate_output_directory(str(output_dir))
        assert result is True
        assert output_dir.exists()
    
    def test_validate_configuration_success(self, temp_dir: Path) -> None:
        """Test comprehensive configuration validation."""
        script_path = temp_dir / "test_script.py"
        script_path.write_text("print('test')")
        
        results = validate_configuration(
            script_path=str(script_path),
            port=8080,
            url="http://localhost:8080",
            output_dir=str(temp_dir),
            check_connectivity=False
        )
        
        assert results["dependencies"] is True
        assert results["script_path"] is True
        assert results["port"] is True
        assert results["url"] is True
        assert results["output_directory"] is True


class TestServerManagement:
    """Test server management functionality."""
    
    @patch('requests.get')
    def test_is_server_running_success(self, mock_get: Mock) -> None:
        """Test is_server_running when server is running."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = is_server_running("http://localhost:8080")
        assert result is True
        mock_get.assert_called_once_with("http://localhost:8080", timeout=2)
    
    @patch('requests.get')
    def test_is_server_running_failure(self, mock_get: Mock) -> None:
        """Test is_server_running when server is not running."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = is_server_running("http://localhost:8080")
        assert result is False
    
    @patch('subprocess.Popen')
    @patch('tests.common.headless_browser.is_server_running')
    def test_start_web_server_success(self, mock_is_running: Mock, mock_popen: Mock, temp_dir: Path) -> None:
        """Test successful web server startup."""
        # Create a test script
        script_path = temp_dir / "test_server.py"
        script_path.write_text("print('Server started')")
        
        # Mock subprocess
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        # Mock server running check
        mock_is_running.return_value = True
        
        result = start_web_server(str(script_path), 8080)
        
        assert result == mock_process
        mock_popen.assert_called_once()
    
    def test_start_web_server_nonexistent_script(self) -> None:
        """Test web server startup with non-existent script."""
        with pytest.raises(ServerStartupError, match="Script not found"):
            start_web_server("nonexistent_script.py", 8080)


class TestScreenshotCapture:
    """Test screenshot capture functionality."""
    
    def test_capture_web_page_screenshot_function_exists(self) -> None:
        """Test that the screenshot capture function exists and is callable."""
        assert callable(capture_web_page_screenshot)
    
    def test_capture_web_page_screenshot_signature(self) -> None:
        """Test that the screenshot capture function has the expected signature."""
        import inspect
        sig = inspect.signature(capture_web_page_screenshot)
        assert 'url' in sig.parameters
        assert 'output_path' in sig.parameters
        assert 'script_path' in sig.parameters
        assert 'port' in sig.parameters


class TestSchedulerScreenshots:
    """Test scheduler-specific screenshot functionality."""
    
    def test_capture_all_scheduler_options_function_exists(self) -> None:
        """Test that the scheduler options capture function exists and is callable."""
        assert callable(capture_all_scheduler_options)
    
    def test_capture_all_scheduler_options_signature(self) -> None:
        """Test that the scheduler options capture function has the expected signature."""
        import inspect
        sig = inspect.signature(capture_all_scheduler_options)
        assert 'base_url' in sig.parameters
        assert 'output_dir' in sig.parameters
        assert 'script_path' in sig.parameters
        assert 'port' in sig.parameters
    
    def test_capture_timeline_screenshots_function_exists(self) -> None:
        """Test that the timeline screenshots capture function exists and is callable."""
        assert callable(capture_timeline_screenshots)
    
    def test_capture_timeline_screenshots_signature(self) -> None:
        """Test that the timeline screenshots capture function has the expected signature."""
        import inspect
        sig = inspect.signature(capture_timeline_screenshots)
        assert 'base_url' in sig.parameters
        assert 'output_dir' in sig.parameters
        assert 'script_path' in sig.parameters
        assert 'port' in sig.parameters


class TestErrorHandling:
    """Test error handling and custom exceptions."""
    
    def test_configuration_error_inheritance(self) -> None:
        """Test that ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_headless_browser_error_inheritance(self) -> None:
        """Test that HeadlessBrowserError inherits from Exception."""
        error = HeadlessBrowserError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_server_startup_error_inheritance(self) -> None:
        """Test that ServerStartupError inherits from HeadlessBrowserError."""
        error = ServerStartupError("Test error")
        assert isinstance(error, HeadlessBrowserError)
        assert str(error) == "Test error"
    
    def test_screenshot_capture_error_inheritance(self) -> None:
        """Test that ScreenshotCaptureError inherits from HeadlessBrowserError."""
        error = ScreenshotCaptureError("Test error")
        assert isinstance(error, HeadlessBrowserError)
        assert str(error) == "Test error"
