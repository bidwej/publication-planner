"""
Save/Load modal component for schedule persistence.
"""

from dash import html, dcc, dash_table
from typing import List, Dict, Any

def create_save_load_modal():
    """Create the save/load modal component."""
    return html.Div([
        # Modal backdrop
        html.Div(id="modal-backdrop", className="modal-backdrop"),
        
        # Modal content
        html.Div([
            # Modal header
            html.Div([
                html.H3("Save/Load Schedule", className="modal-title"),
                html.Button([
                    html.I(className="fas fa-times")
                ], id="close-modal-btn", className="modal-close-btn")
            ], className="modal-header"),
            
            # Modal body
            html.Div([
                # Tabs for Save/Load
                dcc.Tabs([
                    # Save Tab
                    dcc.Tab(label="Save Schedule", children=[
                        html.Div([
                            html.H4("Save Current Schedule", className="tab-title"),
                            html.P("Save your current schedule for later use.", className="tab-description"),
                            
                            html.Div([
                                html.Label("Schedule Name:", className="form-label"),
                                dcc.Input(
                                    id="save-schedule-name",
                                    type="text",
                                    placeholder="Enter schedule name...",
                                    className="form-input"
                                )
                            ], className="form-group"),
                            
                            html.Div([
                                html.Label("Description (optional):", className="form-label"),
                                dcc.Textarea(
                                    id="save-schedule-description",
                                    placeholder="Enter description...",
                                    className="form-textarea"
                                )
                            ], className="form-group"),
                            
                            html.Div([
                                html.Label("Tags (optional):", className="form-label"),
                                dcc.Input(
                                    id="save-schedule-tags",
                                    type="text",
                                    placeholder="Enter tags separated by commas...",
                                    className="form-input"
                                )
                            ], className="form-group"),
                            
                            html.Div([
                                html.Button([
                                    html.I(className="fas fa-save"),
                                    " Save Schedule"
                                ], id="confirm-save-btn", className="btn btn-primary"),
                                html.Button("Cancel", id="cancel-save-btn", className="btn btn-secondary")
                            ], className="modal-actions")
                        ], className="tab-content")
                    ]),
                    
                    # Load Tab
                    dcc.Tab(label="Load Schedule", children=[
                        html.Div([
                            html.H4("Load Saved Schedule", className="tab-title"),
                            html.P("Load a previously saved schedule.", className="tab-description"),
                            
                            html.Div([
                                html.Label("Select Schedule:", className="form-label"),
                                dcc.Dropdown(
                                    id="saved-schedules-list",
                                    options=[],
                                    placeholder="Select a schedule to load...",
                                    className="schedule-dropdown"
                                )
                            ], className="form-group"),
                            
                            # Schedule details
                            html.Div([
                                html.H5("Schedule Details", className="details-title"),
                                html.Div(id="schedule-details", className="schedule-details")
                            ], className="schedule-details-section"),
                            
                            html.Div([
                                html.Button([
                                    html.I(className="fas fa-download"),
                                    " Load Schedule"
                                ], id="confirm-load-btn", className="btn btn-primary"),
                                html.Button("Cancel", id="cancel-load-btn", className="btn btn-secondary"),
                                html.Button([
                                    html.I(className="fas fa-trash"),
                                    " Delete"
                                ], id="delete-schedule-btn", className="btn btn-danger")
                            ], className="modal-actions")
                        ], className="tab-content")
                    ]),
                    
                    # Export Tab
                    dcc.Tab(label="Export", children=[
                        html.Div([
                            html.H4("Export Schedule", className="tab-title"),
                            html.P("Export your schedule in various formats.", className="tab-description"),
                            
                            html.Div([
                                html.Label("Export Format:", className="form-label"),
                                dcc.RadioItems(
                                    id="export-format",
                                    options=[
                                        {'label': 'JSON (Full data)', 'value': 'json'},
                                        {'label': 'CSV (Table format)', 'value': 'csv'},
                                        {'label': 'PDF Report', 'value': 'pdf'},
                                        {'label': 'Excel Spreadsheet', 'value': 'excel'}
                                    ],
                                    value='json',
                                    className="export-options"
                                )
                            ], className="form-group"),
                            
                            html.Div([
                                html.Label("Include:", className="form-label"),
                                dcc.Checklist(
                                    id="export-include",
                                    options=[
                                        {'label': 'Schedule data', 'value': 'schedule'},
                                        {'label': 'Validation results', 'value': 'validation'},
                                        {'label': 'Analytics', 'value': 'analytics'},
                                        {'label': 'Charts (as images)', 'value': 'charts'}
                                    ],
                                    value=['schedule', 'validation'],
                                    className="export-checklist"
                                )
                            ], className="form-group"),
                            
                            html.Div([
                                html.Button([
                                    html.I(className="fas fa-download"),
                                    " Export"
                                ], id="confirm-export-btn", className="btn btn-primary"),
                                html.Button("Cancel", id="cancel-export-btn", className="btn btn-secondary")
                            ], className="modal-actions")
                        ], className="tab-content")
                    ])
                ], id="save-load-tabs", className="modal-tabs")
            ], className="modal-body")
        ], className="modal-content")
    ], id="save-load-modal", className="modal modal-closed")

def create_schedule_details_card(schedule_info: Dict[str, Any]) -> html.Div:
    """Create a card showing schedule details."""
    return html.Div([
        html.Div([
            html.H6("Schedule Information", className="card-title"),
            html.Div([
                html.P([
                    html.Strong("Name: "),
                    schedule_info.get('filename', 'Unknown')
                ]),
                html.P([
                    html.Strong("Strategy: "),
                    schedule_info.get('strategy', 'Unknown')
                ]),
                html.P([
                    html.Strong("Submissions: "),
                    f"{schedule_info.get('submission_count', 0)}"
                ]),
                html.P([
                    html.Strong("Created: "),
                    schedule_info.get('timestamp', 'Unknown')
                ])
            ], className="card-content")
        ], className="schedule-card")
    ])

def create_schedule_preview_table(schedule_data: List[Dict[str, str]]) -> dash_table.DataTable:
    """Create a preview table for the schedule."""
    return dash_table.DataTable(
        id='schedule-preview-table',
        columns=[
            {'name': 'ID', 'id': 'id'},
            {'name': 'Title', 'id': 'title'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Start Date', 'id': 'start_date'},
            {'name': 'Conference', 'id': 'conference'}
        ],
        data=schedule_data[:10],  # Show first 10 entries
        page_size=5,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '8px',
            'fontSize': '12px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold'
        }
    )

def create_export_options() -> html.Div:
    """Create export options section."""
    return html.Div([
        html.H5("Export Options", className="export-title"),
        html.Div([
            html.Div([
                html.Label("File Name:", className="form-label"),
                dcc.Input(
                    id="export-filename",
                    type="text",
                    placeholder="schedule_export",
                    className="form-input"
                )
            ], className="form-group"),
            
            html.Div([
                html.Label("Include Metadata:", className="form-label"),
                dcc.Checklist(
                    id="export-metadata",
                    options=[
                        {'label': 'Configuration', 'value': 'config'},
                        {'label': 'Validation Results', 'value': 'validation'},
                        {'label': 'Analytics', 'value': 'analytics'},
                        {'label': 'Timestamps', 'value': 'timestamps'}
                    ],
                    value=['config', 'validation'],
                    className="export-checklist"
                )
            ], className="form-group")
        ], className="export-options-content")
    ], className="export-options-section")
