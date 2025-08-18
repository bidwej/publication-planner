"""
Main Dash application for Paper Planner.
"""

import argparse
from dash import Dash, html, dcc, Input, Output, callback, page_container
from app.components.dashboard.layout import create_dashboard_layout
from app.components.gantt.layout import create_gantt_layout
from app.components.metrics.layout import create_metrics_layout
from typing import Optional


def create_app(mode: str, data_path: Optional[str] | None = None) -> Dash:
    """Create and configure the Dash application based on mode."""
    app = Dash(__name__, suppress_callback_exceptions=True)
    
    # No local asset loading; config will be fetched via backend API in future
    config = None
    
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
    # Deprecated: data-path (kept for CLI compatibility but unused)
    parser.add_argument('--data-path', type=str, help='[Deprecated] Path to data configuration file')
    
    args = parser.parse_args()
    
    # Create app with specified data path
    app = create_app(args.mode, args.data_path)
    print(f"🚀 Starting Paper Planner in {args.mode.upper()} mode on http://{args.host}:{args.port}")
    app.run(debug=args.debug, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
