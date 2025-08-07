"""Tests for app.layouts.main_content module."""

from dash import html, dcc
from layouts.main_content import create_main_content


class TestMainContentLayout:
    """Test cases for main content layout component."""
    
    def test_create_main_content_returns_main_element(self):
        """Test that create_main_content returns a main element."""
        main_content = create_main_content()
        
        assert isinstance(main_content, html.Main)
        assert main_content.className == "main-content"
    
    def test_main_content_contains_dashboard_header(self):
        """Test that main content contains the dashboard header section."""
        main_content = create_main_content()
        
        # Find the dashboard header
        dashboard_header = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "dashboard-header":
                dashboard_header = child
                break
        
        assert dashboard_header is not None
        assert isinstance(dashboard_header, html.Div)
        
        # Check dashboard title
        dashboard_title = dashboard_header.children[0]
        assert isinstance(dashboard_title, html.H2)
        assert dashboard_title.children == "Schedule Dashboard"
        assert dashboard_title.className == "dashboard-title"
        
        # Check dashboard description
        dashboard_description = dashboard_header.children[1]
        assert isinstance(dashboard_description, html.P)
        assert dashboard_description.children == "Generate and analyze academic paper schedules with interactive visualizations."
        assert dashboard_description.className == "dashboard-description"
    
    def test_main_content_contains_metrics_section(self):
        """Test that main content contains the summary metrics section."""
        main_content = create_main_content()
        
        # Find the metrics section
        metrics_section = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "metrics-section":
                metrics_section = child
                break
        
        assert metrics_section is not None
        assert isinstance(metrics_section, html.Div)
        
        # Check section title
        section_title = metrics_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Summary Metrics"
        assert section_title.className == "section-title"
        
        # Check metrics container
        metrics_container = metrics_section.children[1]
        assert isinstance(metrics_container, html.Div)
        assert metrics_container.id == "summary-metrics"
        assert metrics_container.className == "metrics-container"
    
    def test_main_content_contains_charts_row(self):
        """Test that main content contains the charts row with gantt and metrics charts."""
        main_content = create_main_content()
        
        # Find the charts row
        charts_row = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "charts-row":
                charts_row = child
                break
        
        assert charts_row is not None
        assert isinstance(charts_row, html.Div)
        
        # Check that charts row has 2 chart sections
        chart_sections = charts_row.children
        assert len(chart_sections) == 2
        
        # Check gantt chart section
        gantt_section = chart_sections[0]
        assert isinstance(gantt_section, html.Div)
        assert gantt_section.className == "chart-section"
        
        gantt_title = gantt_section.children[0]
        assert isinstance(gantt_title, html.H3)
        assert gantt_title.children == "Schedule Timeline"
        assert gantt_title.className == "section-title"
        
        gantt_chart = gantt_section.children[1]
        assert isinstance(gantt_chart, dcc.Graph)
        assert gantt_chart.id == "gantt-chart"
        assert gantt_chart.className == "chart-container"
        
        # Check metrics chart section
        metrics_section = chart_sections[1]
        assert isinstance(metrics_section, html.Div)
        assert metrics_section.className == "chart-section"
        
        metrics_title = metrics_section.children[0]
        assert isinstance(metrics_title, html.H3)
        assert metrics_title.children == "Performance Metrics"
        assert metrics_title.className == "section-title"
        
        metrics_chart = metrics_section.children[1]
        assert isinstance(metrics_chart, dcc.Graph)
        assert metrics_chart.id == "metrics-chart"
        assert metrics_chart.className == "chart-container"
    
    def test_main_content_contains_tables_row(self):
        """Test that main content contains the tables row with schedule and violations tables."""
        main_content = create_main_content()
        
        # Find the tables row
        tables_row = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "tables-row":
                tables_row = child
                break
        
        assert tables_row is not None
        assert isinstance(tables_row, html.Div)
        
        # Check that tables row has 2 table sections
        table_sections = tables_row.children
        assert len(table_sections) == 2
        
        # Check schedule table section
        schedule_section = table_sections[0]
        assert isinstance(schedule_section, html.Div)
        assert schedule_section.className == "table-section"
        
        schedule_title = schedule_section.children[0]
        assert isinstance(schedule_title, html.H3)
        assert schedule_title.children == "Schedule Details"
        assert schedule_title.className == "section-title"
        
        # Check schedule table header
        schedule_header = schedule_section.children[1]
        assert isinstance(schedule_header, html.Div)
        assert schedule_header.className == "table-header"
        
        # Check table controls
        table_controls = schedule_header.children[0]
        assert isinstance(table_controls, html.Div)
        assert table_controls.className == "table-controls"
        
        filter_label = table_controls.children[0]
        assert isinstance(filter_label, html.Label)
        assert filter_label.children == "Filter by:"
        
        filter_dropdown = table_controls.children[1]
        assert isinstance(filter_dropdown, dcc.Dropdown)
        assert filter_dropdown.id == "schedule-filter"
        assert filter_dropdown.value == "all"
        assert filter_dropdown.className == "table-filter"
        
        # Check table actions
        table_actions = schedule_header.children[1]
        assert isinstance(table_actions, html.Div)
        assert table_actions.className == "table-actions"
        
        export_btn = table_actions.children[0]
        assert isinstance(export_btn, html.Button)
        assert export_btn.id == "table-export-btn"
        assert export_btn.className == "btn btn-secondary btn-small"
        assert len(export_btn.children) == 2
        assert isinstance(export_btn.children[0], html.I)
        assert export_btn.children[0].className == "fas fa-download"
        assert export_btn.children[1] == " Export CSV"
        
        # Check schedule table loading
        schedule_loading = schedule_section.children[2]
        assert isinstance(schedule_loading, dcc.Loading)
        assert schedule_loading.id == "loading-schedule-table"
        assert schedule_loading.type == "default"
        
        # Check violations table section
        violations_section = table_sections[1]
        assert isinstance(violations_section, html.Div)
        assert violations_section.className == "table-section"
        
        violations_title = violations_section.children[0]
        assert isinstance(violations_title, html.H3)
        assert violations_title.children == "Constraint Violations"
        assert violations_title.className == "section-title"
        
        # Check violations table loading
        violations_loading = violations_section.children[1]
        assert isinstance(violations_loading, dcc.Loading)
        assert violations_loading.id == "loading-violations-table"
        assert violations_loading.type == "default"
    
    def test_main_content_contains_analytics_section(self):
        """Test that main content contains the analytics section."""
        main_content = create_main_content()
        
        # Find the analytics section
        analytics_section = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "analytics-section":
                analytics_section = child
                break
        
        assert analytics_section is not None
        assert isinstance(analytics_section, html.Div)
        
        # Check section title
        section_title = analytics_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Schedule Analytics"
        assert section_title.className == "section-title"
        
        # Check analytics grid
        analytics_grid = analytics_section.children[1]
        assert isinstance(analytics_grid, html.Div)
        assert analytics_grid.className == "analytics-grid"
        
        # Check analytics cards
        analytics_cards = analytics_grid.children
        assert len(analytics_cards) == 3
        
        # Check timeline analytics card
        timeline_card = analytics_cards[0]
        assert isinstance(timeline_card, html.Div)
        assert timeline_card.className == "analytics-card"
        
        timeline_title = timeline_card.children[0]
        assert isinstance(timeline_title, html.H4)
        assert timeline_title.children == "Timeline Analysis"
        assert timeline_title.className == "subsection-title"
        
        timeline_content = timeline_card.children[1]
        assert isinstance(timeline_content, html.Div)
        assert timeline_content.id == "timeline-analytics"
        assert timeline_content.className == "analytics-content"
        
        # Check resource analytics card
        resource_card = analytics_cards[1]
        assert isinstance(resource_card, html.Div)
        assert resource_card.className == "analytics-card"
        
        resource_title = resource_card.children[0]
        assert isinstance(resource_title, html.H4)
        assert resource_title.children == "Resource Utilization"
        assert resource_title.className == "subsection-title"
        
        resource_content = resource_card.children[1]
        assert isinstance(resource_content, html.Div)
        assert resource_content.id == "resource-analytics"
        assert resource_content.className == "analytics-content"
        
        # Check quality analytics card
        quality_card = analytics_cards[2]
        assert isinstance(quality_card, html.Div)
        assert quality_card.className == "analytics-card"
        
        quality_title = quality_card.children[0]
        assert isinstance(quality_title, html.H4)
        assert quality_title.children == "Quality Metrics"
        assert quality_title.className == "subsection-title"
        
        quality_content = quality_card.children[1]
        assert isinstance(quality_content, html.Div)
        assert quality_content.id == "quality-analytics"
        assert quality_content.className == "analytics-content"
    
    def test_main_content_schedule_filter_options(self):
        """Test that schedule filter dropdown has correct options."""
        main_content = create_main_content()
        
        # Find schedule filter dropdown
        filter_dropdown = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "tables-row":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "table-section":
                        for great_grandchild in grandchild.children:
                            if hasattr(great_grandchild, 'className') and great_grandchild.className == "table-header":
                                for great_great_grandchild in great_grandchild.children:
                                    if hasattr(great_great_grandchild, 'className') and great_great_grandchild.className == "table-controls":
                                        for great_great_great_grandchild in great_great_grandchild.children:
                                            if hasattr(great_great_great_grandchild, 'id') and great_great_great_grandchild.id == "schedule-filter":
                                                filter_dropdown = great_great_great_grandchild
                                                break
                                        if filter_dropdown:
                                            break
                                if filter_dropdown:
                                    break
                        if filter_dropdown:
                            break
                if filter_dropdown:
                    break
        
        assert filter_dropdown is not None
        
        # Check options
        expected_options = [
            {'label': 'All Submissions', 'value': 'all'},
            {'label': 'Papers Only', 'value': 'papers'},
            {'label': 'Abstracts Only', 'value': 'abstracts'},
            {'label': 'Mods Only', 'value': 'mods'}
        ]
        
        assert filter_dropdown.options == expected_options
        assert filter_dropdown.value == "all"
    
    def test_main_content_graph_configurations(self):
        """Test that graphs have correct configurations."""
        main_content = create_main_content()
        
        # Find graphs
        graphs = []
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "charts-row":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "chart-section":
                        for great_grandchild in grandchild.children:
                            if isinstance(great_grandchild, dcc.Graph):
                                graphs.append(great_grandchild)
        
        assert len(graphs) == 2
        
        # Check gantt chart configuration
        gantt_chart = graphs[0]
        assert gantt_chart.id == "gantt-chart"
        assert gantt_chart.config['displayModeBar'] == True
        assert gantt_chart.config['displaylogo'] == False
        assert 'pan2d' in gantt_chart.config['modeBarButtonsToRemove']
        assert 'lasso2d' in gantt_chart.config['modeBarButtonsToRemove']
        assert 'select2d' in gantt_chart.config['modeBarButtonsToRemove']
        assert gantt_chart.config['toImageButtonOptions']['format'] == 'png'
        assert gantt_chart.config['toImageButtonOptions']['filename'] == 'schedule_gantt'
        assert gantt_chart.config['toImageButtonOptions']['height'] == 600
        assert gantt_chart.config['toImageButtonOptions']['width'] == 1200
        assert gantt_chart.config['toImageButtonOptions']['scale'] == 2
        
        # Check metrics chart configuration
        metrics_chart = graphs[1]
        assert metrics_chart.id == "metrics-chart"
        assert metrics_chart.config['displayModeBar'] == True
        assert metrics_chart.config['displaylogo'] == False
        assert 'pan2d' in metrics_chart.config['modeBarButtonsToRemove']
        assert 'lasso2d' in metrics_chart.config['modeBarButtonsToRemove']
        assert 'select2d' in metrics_chart.config['modeBarButtonsToRemove']
        assert metrics_chart.config['toImageButtonOptions']['format'] == 'png'
        assert metrics_chart.config['toImageButtonOptions']['filename'] == 'performance_metrics'
        assert metrics_chart.config['toImageButtonOptions']['height'] == 400
        assert metrics_chart.config['toImageButtonOptions']['width'] == 600
        assert metrics_chart.config['toImageButtonOptions']['scale'] == 2
    
    def test_main_content_loading_components(self):
        """Test that loading components have correct structure."""
        main_content = create_main_content()
        
        # Find loading components
        loading_components = []
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "tables-row":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "table-section":
                        for great_grandchild in grandchild.children:
                            if isinstance(great_grandchild, dcc.Loading):
                                loading_components.append(great_grandchild)
        
        assert len(loading_components) == 2
        
        # Check schedule table loading
        schedule_loading = loading_components[0]
        assert schedule_loading.id == "loading-schedule-table"
        assert schedule_loading.type == "default"
        
        schedule_children = schedule_loading.children
        assert len(schedule_children) == 2
        assert isinstance(schedule_children[0], dcc.Store)
        assert schedule_children[0].id == "schedule-table-data"
        assert isinstance(schedule_children[1], html.Div)
        assert schedule_children[1].id == "schedule-table-container"
        
        # Check violations table loading
        violations_loading = loading_components[1]
        assert violations_loading.id == "loading-violations-table"
        assert violations_loading.type == "default"
        
        violations_children = violations_loading.children
        assert len(violations_children) == 2
        assert isinstance(violations_children[0], dcc.Store)
        assert violations_children[0].id == "violations-table-data"
        assert isinstance(violations_children[1], html.Div)
        assert violations_children[1].id == "violations-table-container"
    
    def test_main_content_component_ids_are_unique(self):
        """Test that all main content components have unique IDs."""
        main_content = create_main_content()
        
        # Collect all component IDs recursively
        def collect_ids(component, ids_list):
            if hasattr(component, 'id') and component.id:
                ids_list.append(component.id)
            if hasattr(component, 'children') and component.children:
                if isinstance(component.children, list):
                    for child in component.children:
                        collect_ids(child, ids_list)
                else:
                    collect_ids(component.children, ids_list)
        
        component_ids = []
        collect_ids(main_content, component_ids)
        
        # Check that IDs are unique
        assert len(component_ids) == len(set(component_ids))
        
        # Check specific component IDs
        expected_ids = [
            "summary-metrics",
            "gantt-chart",
            "metrics-chart",
            "schedule-filter",
            "table-export-btn",
            "loading-schedule-table",
            "schedule-table-data",
            "schedule-table-container",
            "loading-violations-table",
            "violations-table-data",
            "violations-table-container",
            "timeline-analytics",
            "resource-analytics",
            "quality-analytics"
        ]
        for expected_id in expected_ids:
            assert expected_id in component_ids
    
    def test_main_content_has_correct_css_classes(self):
        """Test that main content and its components have correct CSS classes."""
        main_content = create_main_content()
        
        # Main content class
        assert main_content.className == "main-content"
        
        # Check section classes
        sections = main_content.children
        assert sections[0].className == "dashboard-header"
        assert sections[1].className == "metrics-section"
        assert sections[2].className == "charts-row"
        assert sections[3].className == "tables-row"
        assert sections[4].className == "analytics-section"
        
        # Check chart section classes
        charts_row = sections[2]
        chart_sections = charts_row.children
        for chart_section in chart_sections:
            assert chart_section.className == "chart-section"
        
        # Check table section classes
        tables_row = sections[3]
        table_sections = tables_row.children
        for table_section in table_sections:
            assert table_section.className == "table-section"
        
        # Check analytics card classes
        analytics_section = sections[4]
        analytics_grid = analytics_section.children[1]
        analytics_cards = analytics_grid.children
        for analytics_card in analytics_cards:
            assert analytics_card.className == "analytics-card"
    
    def test_main_content_button_icon_classes_are_valid(self):
        """Test that main content button icons use valid FontAwesome classes."""
        main_content = create_main_content()
        
        # Find export button
        export_btn = None
        for child in main_content.children:
            if hasattr(child, 'className') and child.className == "tables-row":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "table-section":
                        for great_grandchild in grandchild.children:
                            if hasattr(great_grandchild, 'className') and great_grandchild.className == "table-header":
                                for great_great_grandchild in great_grandchild.children:
                                    if hasattr(great_great_grandchild, 'className') and great_great_grandchild.className == "table-actions":
                                        export_btn = great_great_grandchild.children[0]
                                        break
                                if export_btn:
                                    break
                        if export_btn:
                            break
                if export_btn:
                    break
        
        assert export_btn is not None
        icon = export_btn.children[0]
        assert icon.className == "fas fa-download"
    
    def test_main_content_structure_completeness(self):
        """Test that main content has all required sections in correct order."""
        main_content = create_main_content()
        
        # Check that main content has exactly 5 main sections
        assert len(main_content.children) == 5
        
        # Check section order: header, metrics, charts, tables, analytics
        sections = main_content.children
        assert sections[0].className == "dashboard-header"
        assert sections[1].className == "metrics-section"
        assert sections[2].className == "charts-row"
        assert sections[3].className == "tables-row"
        assert sections[4].className == "analytics-section"
