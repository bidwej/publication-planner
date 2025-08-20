"""
Minimal test Dash app to isolate UTF-8 encoding issue.
"""

from dash import Dash, html

def create_minimal_app():
    """Create a minimal Dash app with no custom components."""
    app = Dash(__name__)
    
    app.layout = html.Div([
        html.H1("Test App"),
        html.P("This is a minimal test app.")
    ])
    
    return app

if __name__ == '__main__':
    app = create_minimal_app()
    print("🚀 Starting minimal test app on http://127.0.0.1:8052")
    app.run(debug=True, port=8052)
