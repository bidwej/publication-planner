"""
Main Dash application for Paper Planner.
"""

import argparse
from dash import Dash
from app.components.dashboard.layout import create_timeline_layout
from app.components.dashboard.layout import create_dashboard_layout
from app.components.metrics.layout import create_metrics_layout


def create_app(mode: str) -> Dash:
    """Create and configure the Dash application based on mode."""
    app = Dash(__name__)
    
    # Set layout based on mode
    layouts = {
        'timeline': create_timeline_layout,
        'dashboard': create_dashboard_layout,
        'metrics': create_metrics_layout
    }
    
    app.layout = layouts[mode]()
    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Paper Planner Web Application')
    parser.add_argument('--port', type=int, default=8050, help='Port to run on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--mode', type=str, choices=['timeline', 'dashboard', 'metrics'], 
                       default='timeline', help='Application mode: timeline (default), dashboard, or metrics')
    
    args = parser.parse_args()
    
    # Create and run app
    app = create_app(args.mode)
    
    print(f"🚀 Starting Paper Planner in {args.mode.upper()} mode on http://{args.host}:{args.port}")
    app.run_server(debug=args.debug, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
