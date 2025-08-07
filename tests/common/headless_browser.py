"""
Headless browser test functions for capturing web app screenshots.
"""

import subprocess
import time
import requests
import sys
import os
import socket
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""

def validate_script_path(script_path: str) -> bool:
    """
    Validate that a script path exists and is executable.
    
    Args:
        script_path: Path to the script to validate
        
    Returns:
        True if script exists and is accessible
        
    Raises:
        ConfigurationError: If script doesn't exist or isn't accessible
    """
    path = Path(script_path)
    
    if not path.exists():
        raise ConfigurationError(f"Script not found: {script_path}")
    
    if not path.is_file():
        raise ConfigurationError(f"Path is not a file: {script_path}")
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        raise ConfigurationError(f"Script not readable: {script_path}")
    
    # Check if it's a Python file or executable
    if not (path.suffix == '.py' or os.access(path, os.X_OK)):
        raise ConfigurationError(f"Script not executable: {script_path}")
    
    return True

def validate_port(port: int) -> bool:
    """
    Validate that a port number is in valid range.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if port is valid
        
    Raises:
        ConfigurationError: If port is invalid
    """
    if not isinstance(port, int):
        raise ConfigurationError(f"Port must be an integer, got: {type(port)}")
    
    if port < 1 or port > 65535:
        raise ConfigurationError(f"Port must be between 1 and 65535, got: {port}")
    
    return True

def validate_url(url: str) -> bool:
    """
    Validate URL format and basic connectivity.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid
        
    Raises:
        ConfigurationError: If URL is invalid
    """
    if not url:
        raise ConfigurationError("URL cannot be empty")
    
    if not url.startswith(('http://', 'https://')):
        raise ConfigurationError(f"URL must start with http:// or https://, got: {url}")
    
    try:
        # Basic URL parsing
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ConfigurationError(f"Invalid URL format: {url}")
    except Exception as e:
        raise ConfigurationError(f"Invalid URL format: {url} - {e}")
    
    return True

def check_port_availability(port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a port is available for binding.
    
    Args:
        port: Port number to check
        host: Host to check (default: localhost)
        
    Returns:
        True if port is available, False if already in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False

def validate_network_connectivity(url: str, timeout: int = 5) -> bool:
    """
    Validate network connectivity to a URL.
    
    Args:
        url: URL to test connectivity to
        timeout: Timeout in seconds
        
    Returns:
        True if connectivity is successful
        
    Raises:
        ConfigurationError: If connectivity fails
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 500  # Accept any non-server error
    except requests.exceptions.ConnectionError:
        raise ConfigurationError(f"Cannot connect to {url} - connection refused")
    except requests.exceptions.Timeout:
        raise ConfigurationError(f"Cannot connect to {url} - timeout after {timeout}s")
    except requests.exceptions.RequestException as e:
        raise ConfigurationError(f"Cannot connect to {url} - {e}")
    except Exception as e:
        raise ConfigurationError(f"Unexpected error connecting to {url}: {e}")

def validate_dependencies() -> bool:
    """
    Validate that required dependencies are available.
    
    Returns:
        True if all dependencies are available
        
    Raises:
        ConfigurationError: If any dependency is missing
    """
    missing_deps = []
    
    # Check for playwright
    try:
        pass
    except ImportError:
        missing_deps.append("playwright")
    
    # Check for requests
    try:
        pass
    except ImportError:
        missing_deps.append("requests")
    
    # Check for asyncio
    try:
        pass
    except ImportError:
        missing_deps.append("asyncio")
    
    if missing_deps:
        raise ConfigurationError(f"Missing required dependencies: {', '.join(missing_deps)}")
    
    return True

def validate_output_directory(output_dir: str) -> bool:
    """
    Validate that output directory can be created and written to.
    
    Args:
        output_dir: Directory path to validate
        
    Returns:
        True if directory is valid and writable
        
    Raises:
        ConfigurationError: If directory cannot be created or written to
    """
    path = Path(output_dir)
    
    try:
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = path / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        
        return True
    except PermissionError:
        raise ConfigurationError(f"Cannot write to output directory: {output_dir}")
    except Exception as e:
        raise ConfigurationError(f"Error with output directory {output_dir}: {e}")

def validate_configuration(
    script_path: Optional[str] = None,
    port: Optional[int] = None,
    url: Optional[str] = None,
    output_dir: Optional[str] = None,
    check_connectivity: bool = True
) -> Dict[str, bool]:
    """
    Comprehensive configuration validation.
    
    Args:
        script_path: Path to script to validate
        port: Port number to validate
        url: URL to validate
        output_dir: Output directory to validate
        check_connectivity: Whether to check network connectivity
        
    Returns:
        Dictionary with validation results
        
    Raises:
        ConfigurationError: If any validation fails
    """
    results = {
        "dependencies": False,
        "script_path": False,
        "port": False,
        "url": False,
        "output_directory": False,
        "network_connectivity": False
    }
    
    try:
        # Validate dependencies
        results["dependencies"] = validate_dependencies()
        
        # Validate script path if provided
        if script_path:
            results["script_path"] = validate_script_path(script_path)
        
        # Validate port if provided
        if port:
            results["port"] = validate_port(port)
            # Check if port is available
            if not check_port_availability(port):
                raise ConfigurationError(f"Port {port} is already in use")
        
        # Validate URL if provided
        if url:
            results["url"] = validate_url(url)
            
            # Check connectivity if requested
            if check_connectivity:
                results["network_connectivity"] = validate_network_connectivity(url)
        
        # Validate output directory if provided
        if output_dir:
            results["output_directory"] = validate_output_directory(output_dir)
        
        return results
        
    except ConfigurationError as e:
        print(f"[ERROR] Configuration validation failed: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error during validation: {e}")
        raise ConfigurationError(f"Validation error: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HeadlessBrowserError(Exception):
    """Custom exception for headless browser operations."""

class ServerStartupError(HeadlessBrowserError):
    """Exception raised when server fails to start."""

class ScreenshotCaptureError(HeadlessBrowserError):
    """Exception raised when screenshot capture fails."""

def is_server_running(url: str, timeout: int = 2) -> bool:
    """Check if a web server is running at the given URL."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.debug(f"Server check failed for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking server {url}: {e}")
        return False

def start_web_server(script_path: str, port: int, max_wait: int = 10) -> Optional[subprocess.Popen]:
    """Start a web server using the given script and wait for it to be ready."""
    logger.info(f"[START] Starting web server on port {port}")
    
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        raise ServerStartupError(error_msg)
    
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        logger.info(f"[WAIT] Waiting for server to start")
        url = f"http://127.0.0.1:{port}"
        
        for i in range(max_wait):
            if is_server_running(url):
                logger.info(f"[OK] Server is running at {url}!")
                return process
            time.sleep(1)
            logger.info(f"   Waiting ({i+1}/{max_wait})")
        
        # If we get here, server didn't start
        error_msg = f"Server failed to start within {max_wait} seconds"
        logger.error(error_msg)
        
        # Try to get error output from the process
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stderr:
                logger.error(f"Server stderr: {stderr.decode()}")
            if stdout:
                logger.info(f"Server stdout: {stdout.decode()}")
        except subprocess.TimeoutExpired:
            process.kill()
        
        raise ServerStartupError(error_msg)
        
    except subprocess.SubprocessError as e:
        error_msg = f"Error starting server: {e}"
        logger.error(error_msg)
        raise ServerStartupError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error starting server: {e}"
        logger.error(error_msg)
        raise ServerStartupError(error_msg)

async def capture_web_page_screenshot(
    url: str,
    output_path: str,
    script_path: Optional[str] = None,
    port: Optional[int] = None,
    wait_for_selector: Optional[str] = None,
    wait_timeout: int = 5000,
    extra_wait: int = 2000,
    full_page: bool = True,
    browser_options: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Capture a screenshot of a web page using headless browser.
    
    Args:
        url: URL to capture
        output_path: Path to save the screenshot
        script_path: Path to script to start server (if needed)
        port: Port number for server (if starting server)
        wait_for_selector: CSS selector to wait for before screenshot
        wait_timeout: Timeout for waiting for selector (ms)
        extra_wait: Extra time to wait after page load (ms)
        full_page: Whether to capture full page or viewport only
        browser_options: Additional browser options
    
    Returns:
        True if successful, False otherwise
    """
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            return False
    
    # Check if server is running, start if needed
    server_was_running = is_server_running(url)
    process = None
    
    try:
        if not server_was_running and script_path and port:
            try:
                process = start_web_server(script_path, port)
            except ServerStartupError as e:
                logger.error(f"[ERROR] Failed to start server: {e}")
                logger.info(f"Please run manually: python {script_path}")
                return False
        elif not server_was_running:
            error_msg = f"Server not running at {url} and no script provided to start it"
            logger.error(error_msg)
            return False
        else:
            logger.info(f"[OK] Server is already running at {url}!")
        
        async with async_playwright() as p:
            # Launch browser with options
            browser_options = browser_options or {}
            try:
                browser = await p.chromium.launch(headless=True, **browser_options)
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                return False
            
            page = await browser.new_page()
            
            logger.info(f"[SEARCH] Capturing screenshot from {url}")
            
            try:
                # Navigate to the page
                await page.goto(url, timeout=30000)  # 30 second timeout
                logger.info("[OK] Loaded page")
                
                # Wait for page to load
                await page.wait_for_load_state('networkidle', timeout=30000)
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=wait_timeout)
                        logger.info(f"[OK] Found selector: {wait_for_selector}")
                    except PlaywrightTimeoutError:
                        logger.warning(f"[WARNING]  Selector {wait_for_selector} not found within timeout")
                    except Exception as e:
                        logger.warning(f"[WARNING]  Error waiting for selector {wait_for_selector}: {e}")
                
                # Extra wait for dynamic content
                if extra_wait > 0:
                    await page.wait_for_timeout(extra_wait)
                
                # Take screenshot
                await page.screenshot(path=output_path, full_page=full_page)
                logger.info(f"[SCREENSHOT] Screenshot saved as '{output_path}'")
                
                # Inspect chart elements (optional)
                await _inspect_chart_elements(page)
                
                logger.info("[OK] Screenshot capture complete!")
                return True
                
            except PlaywrightTimeoutError as e:
                logger.error(f"[ERROR] Timeout error capturing screenshot: {e}")
                return False
            except Exception as e:
                logger.error(f"[ERROR] Error capturing screenshot: {e}")
                return False
            
            finally:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
    
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error in capture_web_page_screenshot: {e}")
        return False
    
    finally:
        # Stop the server process if we started it
        if process:
            logger.info("[STOP] Stopping server")
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info("[OK] Server stopped.")
            except subprocess.TimeoutExpired:
                logger.warning("[WARNING]  Server didn't stop gracefully, forcing kill")
                process.kill()
            except Exception as e:
                logger.warning(f"[WARNING]  Error stopping server: {e}")

async def _inspect_chart_elements(page: Page) -> None:
    """Inspect chart elements and print statistics."""
    logger.info("\n[CHART] INSPECTING CHART ELEMENTS:")
    
    try:
        # Check for shapes (blackout periods)
        shapes = await page.query_selector_all('.shape-group')
        logger.info(f"[SHAPE] Shape groups (blackout periods): {len(shapes)}")
        
        # Check for vlines (holiday lines)
        vlines = await page.query_selector_all('.vline')
        logger.info(f"[LINE] Vertical lines (holidays): {len(vlines)}")
        
        # Check for bars
        bars = await page.query_selector_all('.trace.bars')
        logger.info(f"[CHART] Bar traces: {len(bars)}")
        
        # Check for scatter plots
        scatter = await page.query_selector_all('.trace.scatter')
        logger.info(f"[SCATTER] Scatter traces: {len(scatter)}")
        
    except Exception as e:
        logger.warning(f"[WARNING]  Error inspecting elements: {e}")

async def _debug_dropdown_elements(page: Page, selector: str) -> None:
    """Debug dropdown elements to understand their structure."""
    print(f"\n[SEARCH] DEBUGGING DROPDOWN: {selector}")
    
    try:
        # Check if dropdown exists
        dropdown = await page.query_selector(selector)
        if dropdown:
            print(f"[OK] Dropdown found: {selector}")
            
            # Get dropdown attributes
            attributes = await dropdown.get_attribute('class')
            print(f"📋 Dropdown classes: {attributes}")
            
            # Look for dropdown options
            options = await page.query_selector_all(f'{selector} .Select-option')
            print(f"[TEXT] Found {len(options)} dropdown options")
            
            for i, option in enumerate(options):
                text = await option.text_content()
                print(f"   Option {i+1}: {text}")
                
        else:
            print(f"[ERROR] Dropdown not found: {selector}")
            
    except Exception as e:
        print(f"[WARNING]  Error debugging dropdown: {e}")

async def capture_fallback_screenshot(
    page: Page,
    output_path: Path,
    scheduler_name: str,
    error_message: str
) -> bool:
    """
    Capture a fallback screenshot when scheduler selection fails.
    
    Args:
        page: Playwright page object
        output_path: Directory to save screenshots
        scheduler_name: Name of the scheduler that failed
        error_message: Error message describing the failure
    
    Returns:
        True if fallback screenshot was captured, False otherwise
    """
    try:
        print(f"[REFRESH] Attempting fallback screenshot for {scheduler_name}")
        
        # Take screenshot of current state
        fallback_path = output_path / f"chart_{scheduler_name}_fallback.png"
        await page.screenshot(path=str(fallback_path), full_page=True)
        
        # Create a text file with error information
        error_path = output_path / f"chart_{scheduler_name}_error.txt"
        with open(error_path, 'w') as f:
            f.write(f"Scheduler: {scheduler_name}\n")
            f.write(f"Error: {error_message}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Fallback screenshot: {fallback_path.name}\n")
        
        print(f"[OK] Fallback screenshot saved: {fallback_path.name}")
        print(f"[TEXT] Error details saved: {error_path.name}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Fallback screenshot failed for {scheduler_name}: {e}")
        return False

async def capture_all_scheduler_options(
    base_url: str = "http://127.0.0.1:8050",
    output_dir: str = ".",
    script_path: str = "run_web_charts.py",
    port: int = 8050
) -> Dict[str, bool]:
    """
    Capture a simple screenshot of the dashboard.
    
    Args:
        base_url: Base URL of the web app
        output_dir: Directory to save screenshots
        script_path: Path to script to start server
        port: Port number for server
    
    Returns:
        Dictionary with success status
    """
    
    # Validate configuration before proceeding
    try:
        validation_results = validate_configuration(
            script_path=script_path,
            port=port,
            url=base_url,
            output_dir=output_dir,
            check_connectivity=False  # Don't check connectivity if server isn't running yet
        )
        logger.info("[OK] Configuration validation passed")
    except ConfigurationError as e:
        logger.error(f"[ERROR] Configuration validation failed: {e}")
        return {}
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    results = {}
    
    # Start server if not running
    if not is_server_running(base_url):
        process = start_web_server(script_path, port)
        if not process:
            print("[ERROR] Failed to start server")
            return {"dashboard": False}
    else:
        process = None
        print("[OK] Server is already running!")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the app
            await page.goto(base_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)  # Wait for page to fully load
            
            # Take simple screenshot
            screenshot_path = output_path / "web_dashboard.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[OK] Saved dashboard screenshot")
            
            results["dashboard"] = True
            
            await browser.close()
    
    finally:
        # Stop server if we started it
        if process:
            print("[STOP] Stopping server")
            process.terminate()
            process.wait()
    
    return results

async def capture_timeline_screenshots(
    base_url: str = "http://127.0.0.1:8051",
    output_dir: str = ".",
    script_path: str = "run_web_charts.py",
    port: int = 8051
) -> bool:
    """
    Capture timeline dashboard screenshots.
    
    Args:
        base_url: Base URL of the timeline app
        output_dir: Directory to save screenshots
        script_path: Path to script to start timeline server
        port: Port number for timeline server
    
    Returns:
        True if successful, False otherwise
    """
    
    # Validate configuration before proceeding
    try:
        validation_results = validate_configuration(
            script_path=script_path,
            port=port,
            url=base_url,
            output_dir=output_dir,
            check_connectivity=False  # Don't check connectivity if server isn't running yet
        )
        logger.info("[OK] Configuration validation passed")
    except ConfigurationError as e:
        logger.error(f"[ERROR] Configuration validation failed: {e}")
        return False
    
    # Create output directory
    output_path = Path(output_dir)
    try:
        output_path.mkdir(exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        return False
    
    # Capture timeline screenshot - simplified without waiting for specific selector
    success = await capture_web_page_screenshot(
        url=base_url,
        output_path=str(output_path / "web_timeline.png"),
        script_path=script_path,
        port=port,
        extra_wait=3000
    )
    
    return success
