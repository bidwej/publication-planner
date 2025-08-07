"""Tests for headless browser functionality."""

import pytest
import socket
import os
import sys
from unittest.mock import AsyncMock, Mock, patch
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
    
    def test_validate_script_path_valid(self, temp_dir):
        """Test validating a valid script path."""
        script_path = temp_dir / "test_script.py"
        script_path.write_text("print('test')")
        
        result = validate_script_path(str(script_path))
        assert result is True
    
    def test_validate_script_path_nonexistent(self):
        """Test validating a non-existent script path."""
        with pytest.raises(ConfigurationError, match="Script not found"):
            validate_script_path("nonexistent_script.py")
    
    def test_validate_script_path_not_file(self, temp_dir):
        """Test validating a path that is not a file."""
        dir_path = temp_dir / "test_dir"
        dir_path.mkdir()
        
        with pytest.raises(ConfigurationError, match="Path is not a file"):
            validate_script_path(str(dir_path))
    
    def test_validate_script_path_not_readable(self, temp_dir):
        """Test validating a script that is not readable."""
        script_path = temp_dir / "test_script.py"
        script_path.write_text("print('test')")
        
        # Make file not readable
        os.chmod(script_path, 0o000)
        
        try:
            with pytest.raises(ConfigurationError, match="Script not readable"):
                validate_script_path(str(script_path))
        finally:
            # Restore permissions
            os.chmod(script_path, 0o644)
    
    def test_validate_port_valid(self):
        """Test validating valid port numbers."""
        assert validate_port(8080) is True
        assert validate_port(1) is True
        assert validate_port(65535) is True
    
    def test_validate_port_invalid_type(self):
        """Test validating port with invalid type."""
        with pytest.raises(ConfigurationError, match="Port must be an integer"):
            validate_port("8080")
    
    def test_validate_port_out_of_range(self):
        """Test validating port numbers out of range."""
        with pytest.raises(ConfigurationError, match="Port must be between 1 and 65535"):
            validate_port(0)
        
        with pytest.raises(ConfigurationError, match="Port must be between 1 and 65535"):
            validate_port(65536)
    
    def test_validate_url_valid(self):
        """Test validating valid URLs."""
        assert validate_url("http://localhost:8080") is True
        assert validate_url("https://example.com") is True
        assert validate_url("http://127.0.0.1:3000") is True
    
    def test_validate_url_empty(self):
        """Test validating empty URL."""
        with pytest.raises(ConfigurationError, match="URL cannot be empty"):
            validate_url("")
    
    def test_validate_url_invalid_protocol(self):
        """Test validating URL with invalid protocol."""
        with pytest.raises(ConfigurationError, match="URL must start with http:// or https://"):
            validate_url("ftp://example.com")
    
    def test_validate_url_invalid_format(self):
        """Test validating URL with invalid format."""
        with pytest.raises(ConfigurationError, match="Invalid URL format"):
            validate_url("not-a-url")
    
    def test_check_port_availability_available(self):
        """Test checking port availability when port is available."""
        # Find an available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        assert check_port_availability(available_port) is True
    
    def test_check_port_availability_in_use(self):
        """Test checking port availability when port is in use."""
        # Create a socket to occupy a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            occupied_port = s.getsockname()[1]
            
            # Port should appear as unavailable
            assert check_port_availability(occupied_port) is False
    
    @patch('requests.get')
    def test_validate_network_connectivity_success(self, mock_get):
        """Test network connectivity validation with successful connection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = validate_network_connectivity("http://example.com")
        assert result is True
    
    @patch('requests.get')
    def test_validate_network_connectivity_server_error(self, mock_get):
        """Test network connectivity validation with server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = validate_network_connectivity("http://example.com")
        assert result is True  # Should accept non-server errors
    
    @patch('requests.get')
    def test_validate_network_connectivity_connection_error(self, mock_get):
        """Test network connectivity validation with connection error."""
        from requests.exceptions import ConnectionError
        mock_get.side_effect = ConnectionError("Connection refused")
        
        with pytest.raises(ConfigurationError, match="Cannot connect to.*connection refused"):
            validate_network_connectivity("http://example.com")
    
    @patch('requests.get')
    def test_validate_network_connectivity_timeout(self, mock_get):
        """Test network connectivity validation with timeout."""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("Request timed out")
        
        with pytest.raises(ConfigurationError, match="Cannot connect to.*timeout"):
            validate_network_connectivity("http://example.com")
    
    def test_validate_dependencies_success(self):
        """Test dependency validation when all dependencies are available."""
        result = validate_dependencies()
        assert result is True
    
    @patch('builtins.__import__')
    def test_validate_dependencies_missing(self, mock_import):
        """Test dependency validation when dependencies are missing."""
        mock_import.side_effect = ImportError("No module named 'playwright'")
        
        with pytest.raises(ConfigurationError, match="Missing required dependencies"):
            validate_dependencies()
    
    def test_validate_output_directory_success(self, temp_dir):
        """Test output directory validation with valid directory."""
        output_dir = temp_dir / "output"
        
        result = validate_output_directory(str(output_dir))
        assert result is True
        assert output_dir.exists()
    
    def test_validate_output_directory_permission_error(self, temp_dir):
        """Test output directory validation with permission error."""
        # Create a directory and make it read-only
        output_dir = temp_dir / "readonly"
        output_dir.mkdir()
        os.chmod(output_dir, 0o444)  # Read-only
        
        try:
            with pytest.raises(ConfigurationError, match="Cannot write to output directory"):
                validate_output_directory(str(output_dir))
        finally:
            # Restore permissions
            os.chmod(output_dir, 0o755)
    
    def test_validate_configuration_success(self, temp_dir):
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
    
    def test_validate_configuration_failure(self):
        """Test configuration validation with invalid parameters."""
        with pytest.raises(ConfigurationError):
            validate_configuration(
                script_path="nonexistent.py",
                port=0,  # Invalid port
                url="invalid-url",
                output_dir="/nonexistent/path"
            )


class TestServerManagement:
    """Test server management functionality."""
    
    @patch('tests.common.headless_browser.is_server_running')
    def test_is_server_running_success(self, mock_is_running):
        """Test server running check when server is running."""
        mock_is_running.return_value = True
        
        result = is_server_running("http://localhost:8080")
        assert result is True
    
    @patch('tests.common.headless_browser.is_server_running')
    def test_is_server_running_failure(self, mock_is_running):
        """Test server running check when server is not running."""
        mock_is_running.return_value = False
        
        result = is_server_running("http://localhost:8080")
        assert result is False
    
    @patch('subprocess.Popen')
    @patch('tests.common.headless_browser.is_server_running')
    def test_start_web_server_success(self, mock_is_running, mock_popen, temp_dir):
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
    
    @patch('subprocess.Popen')
    @patch('tests.common.headless_browser.is_server_running')
    def test_start_web_server_timeout(self, mock_is_running, mock_popen, temp_dir):
        """Test web server startup with timeout."""
        # Create a test script
        script_path = temp_dir / "test_server.py"
        script_path.write_text("print('Server started')")
        
        # Mock subprocess
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        # Mock server running check to always return False (timeout)
        mock_is_running.return_value = False
        
        with pytest.raises(ServerStartupError, match="Server failed to start within"):
            start_web_server(str(script_path), 8080)
    
    def test_start_web_server_nonexistent_script(self):
        """Test web server startup with non-existent script."""
        with pytest.raises(ServerStartupError, match="Script not found"):
            start_web_server("nonexistent_script.py", 8080)


class TestScreenshotCapture:
    """Test screenshot capture functionality."""
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_web_page_screenshot_success(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test successful screenshot capture."""
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test screenshot capture
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080
        )
        
        assert result is True
        mock_page.goto.assert_called_once_with("http://localhost:8080", timeout=30000)
        mock_page.screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_web_page_screenshot_server_already_running(
        self, mock_playwright, mock_is_running, temp_dir
    ):
        """Test screenshot capture when server is already running."""
        # Mock server is already running
        mock_is_running.return_value = True
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test screenshot capture
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path)
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    async def test_capture_web_page_screenshot_no_server_no_script(
        self, mock_is_running, temp_dir
    ):
        """Test screenshot capture when server is not running and no script provided."""
        # Mock server is not running
        mock_is_running.return_value = False
        
        # Test screenshot capture without script
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path)
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_web_page_screenshot_timeout_error(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test screenshot capture with timeout error."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright with timeout error
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Navigation timeout")
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test screenshot capture
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_web_page_screenshot_with_wait_for_selector(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test screenshot capture with wait for selector."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test screenshot capture with selector
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080,
            wait_for_selector=".chart-container"
        )
        
        assert result is True
        mock_page.wait_for_selector.assert_called_once_with(".chart-container", timeout=5000)
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_web_page_screenshot_selector_timeout(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test screenshot capture with selector timeout."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright with selector timeout
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.wait_for_selector.side_effect = PlaywrightTimeoutError("Selector timeout")
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test screenshot capture with selector
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080,
            wait_for_selector=".chart-container"
        )
        
        # Should still succeed even with selector timeout
        assert result is True


class TestSchedulerScreenshots:
    """Test scheduler-specific screenshot functionality."""
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_all_scheduler_options_success(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test successful capture of all scheduler options."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test scheduler options capture
        result = await capture_all_scheduler_options(
            base_url="http://localhost:8050",
            output_dir=str(temp_dir),
            script_path="test_script.py",
            port=8050
        )
        
        assert result["dashboard"] is True
        mock_page.screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    async def test_capture_all_scheduler_options_server_failure(
        self, mock_start_server, mock_is_running
    ):
        """Test scheduler options capture when server fails to start."""
        # Mock server startup failure
        mock_start_server.side_effect = ServerStartupError("Server failed to start")
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Test scheduler options capture
        result = await capture_all_scheduler_options(
            base_url="http://localhost:8050",
            script_path="test_script.py",
            port=8050
        )
        
        assert result == {"dashboard": False}
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_capture_timeline_screenshots_success(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test successful timeline screenshot capture."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test timeline screenshot capture
        result = await capture_timeline_screenshots(
            base_url="http://localhost:8051",
            output_dir=str(temp_dir),
            script_path="test_script.py",
            port=8051
        )
        
        assert result is True
        mock_page.screenshot.assert_called_once()


class TestErrorHandling:
    """Test error handling and custom exceptions."""
    
    def test_configuration_error_inheritance(self):
        """Test that ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_headless_browser_error_inheritance(self):
        """Test that HeadlessBrowserError inherits from Exception."""
        error = HeadlessBrowserError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_server_startup_error_inheritance(self):
        """Test that ServerStartupError inherits from HeadlessBrowserError."""
        error = ServerStartupError("Test error")
        assert isinstance(error, HeadlessBrowserError)
        assert str(error) == "Test error"
    
    def test_screenshot_capture_error_inheritance(self):
        """Test that ScreenshotCaptureError inherits from HeadlessBrowserError."""
        error = ScreenshotCaptureError("Test error")
        assert isinstance(error, HeadlessBrowserError)
        assert str(error) == "Test error"


class TestIntegration:
    """Integration tests for headless browser functionality."""
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.validate_configuration')
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_full_screenshot_workflow(
        self, mock_playwright, mock_start_server, mock_is_running, 
        mock_validate_config, temp_dir
    ):
        """Test the full screenshot capture workflow."""
        # Mock validation
        mock_validate_config.return_value = {
            "dependencies": True,
            "script_path": True,
            "port": True,
            "url": True,
            "output_directory": True,
            "network_connectivity": True
        }
        
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test full workflow
        output_path = temp_dir / "integration_screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080,
            wait_for_selector=".chart-container",
            extra_wait=2000,
            full_page=True
        )
        
        assert result is True
        
        # Verify all expected calls were made
        mock_validate_config.assert_called_once()
        mock_start_server.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_page.wait_for_load_state.assert_called_once()
        mock_page.wait_for_selector.assert_called_once()
        mock_page.wait_for_timeout.assert_called_once_with(2000)
        mock_page.screenshot.assert_called_once()
        mock_browser.close.assert_called_once()
    
    def test_port_availability_integration(self):
        """Test port availability checking in real environment."""
        # Test with a port that should be available
        available_port = 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            available_port = s.getsockname()[1]
        
        assert check_port_availability(available_port) is True
    
    def test_script_path_validation_integration(self, temp_dir):
        """Test script path validation with real file system."""
        # Create a valid script
        script_path = temp_dir / "valid_script.py"
        script_path.write_text("print('Hello, World!')")
        
        assert validate_script_path(str(script_path)) is True
        
        # Test with non-existent script
        with pytest.raises(ConfigurationError):
            validate_script_path(str(temp_dir / "nonexistent.py"))
    
    def test_output_directory_validation_integration(self, temp_dir):
        """Test output directory validation with real file system."""
        # Test with valid directory
        output_dir = temp_dir / "output"
        assert validate_output_directory(str(output_dir)) is True
        assert output_dir.exists()
        
        # Test with existing directory
        assert validate_output_directory(str(temp_dir)) is True


class TestBrowserAutomation:
    """Test browser automation features."""
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_browser_options_customization(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test browser options customization."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test with custom browser options
        output_path = temp_dir / "screenshot.png"
        browser_options = {
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
            "viewport": {"width": 1920, "height": 1080}
        }
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080,
            browser_options=browser_options
        )
        
        assert result is True
        mock_playwright_instance.chromium.launch.assert_called_once_with(
            headless=True, **browser_options
        )
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_browser_launch_failure(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test handling of browser launch failure."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright with launch failure
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.side_effect = Exception("Browser launch failed")
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test browser launch failure
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('tests.common.headless_browser.is_server_running')
    @patch('tests.common.headless_browser.start_web_server')
    @patch('playwright.async_api.async_playwright')
    async def test_page_navigation_timeout(
        self, mock_playwright, mock_start_server, mock_is_running, temp_dir
    ):
        """Test handling of page navigation timeout."""
        # Mock server startup
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock server is not running initially
        mock_is_running.return_value = False
        
        # Mock playwright with navigation timeout
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Navigation timeout")
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        # Test navigation timeout
        output_path = temp_dir / "screenshot.png"
        
        result = await capture_web_page_screenshot(
            url="http://localhost:8080",
            output_path=str(output_path),
            script_path="test_script.py",
            port=8080
        )
        
        assert result is False
