#!/usr/bin/env python3
"""Paper Planner Dash Server - Launch Dash web interfaces."""

import argparse
import logging
import sys
from typing import Dict, NoReturn

# Configure logging with proper formatting and file output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dash_server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Port configuration for each Dash web interface
PORTS: Dict[str, int] = {
    'dashboard': 8050,
    'gantt': 8051,
    'metrics': 8052
}

def run_dash_interface(mode: str, port: int) -> int:
    """Run Dash web interface with proper error handling.
    
    Args:
        mode: The Dash web interface mode to run
        port: Port number to run on
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info(f"Starting {mode} Dash interface on port {port}")
        logger.info(f"Dash interface will be available at: http://127.0.0.1:{port}")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("-" * 50)
        
        # Set up command line arguments for the Dash app
        sys.argv = ['main.py', '--port', str(port), '--mode', mode]
        
        # Import and run the main function from app-dash
        from app_dash.main import main
        main()
        
        logger.info(f"{mode} Dash interface stopped")
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import Dash app: {e}")
        logger.error("Make sure you're in the project root directory")
        logger.error("Check that app-dash is properly installed")
        return 1
        
    except KeyboardInterrupt:
        logger.info(f"{mode} Dash interface stopped by user")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to start {mode} Dash interface: {e}")
        logger.error("Check the logs for more details")
        return 1

def validate_mode(mode: str) -> bool:
    """Validate that the specified mode is supported.
    
    Args:
        mode: The mode to validate
        
    Returns:
        True if mode is valid, False otherwise
    """
    if mode not in PORTS:
        logger.error(f"Invalid mode: {mode}")
        logger.error(f"Supported modes: {', '.join(PORTS.keys())}")
        return False
    return True

def check_dependencies() -> bool:
    """Check if required Dash dependencies are available.
    
    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        import app_dash_backup.main
        return True
    except ImportError as e:
        logger.error(f"Missing Dash dependencies: {e}")
        logger.error("Make sure you're in the project root directory")
        logger.error("Check that app-dash-backup is properly installed")
        return False

def main() -> NoReturn:
    """Main entry point for Dash server with proper argument parsing and error handling."""
    parser = argparse.ArgumentParser(
        description="Paper Planner Dash Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dash_server.py dashboard    # Launch Dash dashboard on port 8050
  python dash_server.py gantt        # Launch Dash timeline on port 8051
  python dash_server.py metrics      # Launch Dash metrics on port 8052
        """
    )
    
    parser.add_argument(
        'mode',
        choices=list(PORTS.keys()),
        help='Dash web interface mode to run'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Custom port number (overrides default)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    # Validate mode
    if not validate_mode(args.mode):
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Determine port
    port = args.port if args.port else PORTS[args.mode]
    
    # Set debug level if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Run the Dash interface
    exit_code = run_dash_interface(args.mode, port)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
