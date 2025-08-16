"""
Main Dash application for Paper Planner.
"""

import argparse
from pathlib import Path
from dash import Dash, html, dcc, Input, Output, callback, page_container
from app.components.dashboard.layout import create_dashboard_layout
from app.components.gantt.layout import create_gantt_layout
from app.components.metrics.layout import create_metrics_layout
from src.core.config import load_config

# Global constant for data path
DEFAULT_DATA_PATH = "app/assets/demo/data/config.json"


def create_app(mode: str, data_path: str | None = None) -> Dash:
    """Create and configure the Dash application based on mode."""
    app = Dash(__name__, suppress_callback_exceptions=True)
    
    # Load data
    config = None
    try:
        target_path = Path(data_path or DEFAULT_DATA_PATH)
        if target_path.exists():
            config = load_config(str(target_path))
            print(f"✅ Data loaded: {len(config.submissions)} submissions, {len(config.conferences)} conferences")
    except Exception as e:
        print(f"❌ Data load failed: {e}")
    
    # Set layout
    layouts = {
        'gantt': create_gantt_layout,
        'dashboard': create_dashboard_layout,
        'metrics': create_metrics_layout
    }
    
    if mode not in layouts:
        raise ValueError(f"Unknown mode: {mode}")
    
    app.layout = layouts[mode](config)
    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Paper Planner Web Application')
    parser.add_argument('--port', type=int, default=8050, help='Port to run on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--mode', type=str, choices=['gantt', 'dashboard', 'metrics'], 
                       default='gantt', help='Application mode: gantt (default), dashboard, or metrics')
    parser.add_argument('--data-path', type=str, help='Custom path to data configuration file')
    
    args = parser.parse_args()
    
    # Create app with specified data path
    app = create_app(args.mode, args.data_path)
    print(f"🚀 Starting Paper Planner in {args.mode.upper()} mode on http://{args.host}:{args.port}")
    app.run(debug=args.debug, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
