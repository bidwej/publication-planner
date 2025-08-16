"""
Chart export functionality for Paper Planner.
Handles PNG and HTML export of charts with proper configuration.
"""

from pathlib import Path
from typing import Any, Optional
from plotly.graph_objs import Figure


def export_chart_png(fig: Figure, filename: str, output_dir: Optional[str] = None) -> Optional[str]:
    """Export a chart as PNG using headless server."""
    try:
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / filename
        else:
            output_path = Path(filename)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as PNG using headless server (as per user preferences)
        fig.write_image(str(output_path), engine="kaleido")
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating PNG: {e}")
        return None


def export_chart_html(fig: Figure, filename: str, output_dir: Optional[str] = None) -> Optional[str]:
    """Export a chart as HTML."""
    try:
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / filename
        else:
            output_path = Path(filename)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as HTML
        fig.write_html(str(output_path))
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating HTML: {e}")
        return None
