#!/usr/bin/env python3
"""Paper Planner Frontend Runner - Elegant launcher for Dash interfaces."""

import argparse
import sys
import os
from pathlib import Path

# Interface configuration
INTERFACES = {
    'dashboard': {'port': 8050, 'desc': 'Main dashboard with overview metrics'},
    'gantt': {'port': 8051, 'desc': 'Gantt chart timeline visualization'},
    'metrics': {'port': 8052, 'desc': 'Detailed metrics and analytics'}
}

def setup_env():
    """Check backend installation."""
    try:
        from core.models import Config
        print("✓ Backend ready")
        return True
    except ImportError:
        print("❌ Backend not available - install with: pip install -e ../backend")
        return False

def run_interface(name: str, port: int, debug: bool = False):
    """Run the specified Dash interface."""
    try:
        info = INTERFACES[name]
        print(f"\n🚀 {name.upper()} on port {port}")
        print(f"📍 {info['desc']}")
        print(f"🌐 http://127.0.0.1:{port}")
        print("⏹️  Ctrl+C to stop")
        print("-" * 50)
        
        from app.main import create_app
        app = create_app(name)
        app.run(debug=debug, host='127.0.0.1', port=port, use_reloader=False)
        
    except KeyboardInterrupt:
        print(f"\n⏹️  {name} stopped")
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return 1
    return 0

def main():
    parser = argparse.ArgumentParser(description="Paper Planner Frontend")
    parser.add_argument('interface', nargs='?', choices=INTERFACES.keys(), help='Interface to run')
    parser.add_argument('--list', action='store_true', help='List interfaces')
    parser.add_argument('--port', type=int, help='Custom port')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 Available Interfaces:")
        for name, info in INTERFACES.items():
            print(f"  {name}: {info['desc']} (port {info['port']})")
        return
    
    if not args.interface:
        print("❌ Please specify interface: dashboard, gantt, or metrics")
        return
    
    if not setup_env():
        sys.exit(1)
    
    port = args.port or INTERFACES[args.interface]['port']
    sys.exit(run_interface(args.interface, port, args.debug))

if __name__ == "__main__":
    main()
