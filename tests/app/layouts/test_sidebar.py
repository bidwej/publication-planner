"""Tests for app.layouts.sidebar module."""

from dash import html, dcc
from layouts.sidebar import create_sidebar
from core.models import SchedulerStrategy


class TestSidebarLayout:
    """Test cases for sidebar layout component."""
    
    def test_create_sidebar_returns_aside_element(self):
        """Test that create_sidebar returns an aside element."""
        sidebar = create_sidebar()
        
        assert isinstance(sidebar, html.Aside)
        assert sidebar.className == "sidebar"
    
    def test_sidebar_contains_strategy_section(self):
        """Test that sidebar contains the strategy selection section."""
        sidebar = create_sidebar()
        
        # Find the strategy section
        strategy_section = None
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                # Check if this section contains strategy dropdown
                for grandchild in child.children:
                    if hasattr(grandchild, 'id') and grandchild.id == "strategy-selector":
                        strategy_section = child
                        break
                if strategy_section:
                    break
        
        assert strategy_section is not None
        assert isinstance(strategy_section, html.Div)
        
        # Check section title
        section_title = strategy_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Scheduling Strategy"
        assert section_title.className == "sidebar-section-title"
        
        # Check strategy dropdown
        strategy_dropdown = strategy_section.children[1]
        assert isinstance(strategy_dropdown, dcc.Dropdown)
        assert strategy_dropdown.id == "strategy-selector"
        assert strategy_dropdown.value == SchedulerStrategy.GREEDY.value
        assert strategy_dropdown.placeholder == "Select strategy"
        assert strategy_dropdown.className == "strategy-dropdown"
        
        # Check generate button
        generate_btn = strategy_section.children[2]
        assert isinstance(generate_btn, html.Button)
        assert generate_btn.id == "generate-schedule-btn"
        assert generate_btn.className == "btn btn-primary btn-full"
        assert len(generate_btn.children) == 2
        assert isinstance(generate_btn.children[0], html.I)
        assert generate_btn.children[0].className == "fas fa-play"
        assert generate_btn.children[1] == " Generate Schedule"
    
    def test_sidebar_contains_configuration_section(self):
        """Test that sidebar contains the configuration section with sliders."""
        sidebar = create_sidebar()
        
        # Find the configuration section
        config_section = None
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                # Check if this section contains configuration sliders
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "control-group":
                        config_section = child
                        break
                if config_section:
                    break
        
        assert config_section is not None
        assert isinstance(config_section, html.Div)
        
        # Check section title
        section_title = config_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Configuration"
        assert section_title.className == "sidebar-section-title"
        
        # Check control groups
        control_groups = config_section.children[1:]
        assert len(control_groups) == 3
        
        # Check max concurrent slider
        max_concurrent_group = control_groups[0]
        assert max_concurrent_group.className == "control-group"
        assert len(max_concurrent_group.children) == 2
        
        max_concurrent_label = max_concurrent_group.children[0]
        assert isinstance(max_concurrent_label, html.Label)
        assert max_concurrent_label.children == "Max Concurrent Submissions:"
        
        max_concurrent_slider = max_concurrent_group.children[1]
        assert isinstance(max_concurrent_slider, dcc.Slider)
        assert max_concurrent_slider.id == "max-concurrent-slider"
        assert max_concurrent_slider.min == 1
        assert max_concurrent_slider.max == 5
        assert max_concurrent_slider.step == 1
        assert max_concurrent_slider.value == 2
        assert max_concurrent_slider.className == "config-slider"
        
        # Check paper lead time slider
        paper_lead_group = control_groups[1]
        paper_lead_slider = paper_lead_group.children[1]
        assert isinstance(paper_lead_slider, dcc.Slider)
        assert paper_lead_slider.id == "paper-lead-time-slider"
        assert paper_lead_slider.min == 1
        assert paper_lead_slider.max == 6
        assert paper_lead_slider.step == 1
        assert paper_lead_slider.value == 3
        assert paper_lead_slider.className == "config-slider"
        
        # Check abstract lead time slider
        abstract_lead_group = control_groups[2]
        abstract_lead_slider = abstract_lead_group.children[1]
        assert isinstance(abstract_lead_slider, dcc.Slider)
        assert abstract_lead_slider.id == "abstract-lead-time-slider"
        assert abstract_lead_slider.min == 0
        assert abstract_lead_slider.max == 60
        assert abstract_lead_slider.step == 5
        assert abstract_lead_slider.value == 30
        assert abstract_lead_slider.className == "config-slider"
    
    def test_sidebar_contains_options_section(self):
        """Test that sidebar contains the options section with checklists."""
        sidebar = create_sidebar()
        
        # Find the options section
        options_section = None
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                # Check if this section contains option checklists
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "control-group":
                        # Check if this control group contains a checklist
                        for great_grandchild in grandchild.children:
                            if hasattr(great_grandchild, 'id') and 'enable-' in great_grandchild.id:
                                options_section = child
                                break
                        if options_section:
                            break
                if options_section:
                    break
        
        assert options_section is not None
        assert isinstance(options_section, html.Div)
        
        # Check section title
        section_title = options_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Options"
        assert section_title.className == "sidebar-section-title"
        
        # Check control groups
        control_groups = options_section.children[1:]
        assert len(control_groups) == 3
        
        # Check blackout dates checklist
        blackout_group = control_groups[0]
        blackout_checklist = blackout_group.children[0]
        assert isinstance(blackout_checklist, dcc.Checklist)
        assert blackout_checklist.id == "enable-blackout-dates"
        assert blackout_checklist.value == ['enabled']
        assert blackout_checklist.className == "option-checklist"
        
        # Check dependencies checklist
        deps_group = control_groups[1]
        deps_checklist = deps_group.children[0]
        assert isinstance(deps_checklist, dcc.Checklist)
        assert deps_checklist.id == "enable-dependencies"
        assert deps_checklist.value == ['enabled']
        assert deps_checklist.className == "option-checklist"
        
        # Check engineering priority checklist
        eng_group = control_groups[2]
        eng_checklist = eng_group.children[0]
        assert isinstance(eng_checklist, dcc.Checklist)
        assert eng_checklist.id == "enable-engineering-priority"
        assert eng_checklist.value == []
        assert eng_checklist.className == "option-checklist"
    
    def test_sidebar_contains_actions_section(self):
        """Test that sidebar contains the actions section with buttons."""
        sidebar = create_sidebar()
        
        # Find the actions section (last section with action buttons)
        actions_section = None
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                # Check if this section contains action buttons
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and 'btn btn-' in grandchild.className:
                        actions_section = child
                        break
                if actions_section:
                    break
        
        assert actions_section is not None
        assert isinstance(actions_section, html.Div)
        
        # Check section title
        section_title = actions_section.children[0]
        assert isinstance(section_title, html.H3)
        assert section_title.children == "Actions"
        assert section_title.className == "sidebar-section-title"
        
        # Check action buttons
        action_buttons = actions_section.children[1:]
        assert len(action_buttons) == 4
        
        # Check save schedule button
        save_btn = action_buttons[0]
        assert isinstance(save_btn, html.Button)
        assert save_btn.id == "save-schedule-btn"
        assert save_btn.className == "btn btn-secondary btn-full"
        assert len(save_btn.children) == 2
        assert isinstance(save_btn.children[0], html.I)
        assert save_btn.children[0].className == "fas fa-save"
        assert save_btn.children[1] == " Save Schedule"
        
        # Check load schedule button
        load_btn = action_buttons[1]
        assert isinstance(load_btn, html.Button)
        assert load_btn.id == "load-schedule-btn"
        assert load_btn.className == "btn btn-secondary btn-full"
        assert len(load_btn.children) == 2
        assert isinstance(load_btn.children[0], html.I)
        assert load_btn.children[0].className == "fas fa-folder-open"
        assert load_btn.children[1] == " Load Schedule"
        
        # Check export CSV button
        export_btn = action_buttons[2]
        assert isinstance(export_btn, html.Button)
        assert export_btn.id == "export-schedule-btn"
        assert export_btn.className == "btn btn-secondary btn-full"
        assert len(export_btn.children) == 2
        assert isinstance(export_btn.children[0], html.I)
        assert export_btn.children[0].className == "fas fa-download"
        assert export_btn.children[1] == " Export CSV"
        
        # Check print report button
        print_btn = action_buttons[3]
        assert isinstance(print_btn, html.Button)
        assert print_btn.id == "print-report-btn"
        assert print_btn.className == "btn btn-secondary btn-full"
        assert len(print_btn.children) == 2
        assert isinstance(print_btn.children[0], html.I)
        assert print_btn.children[0].className == "fas fa-print"
        assert print_btn.children[1] == " Print Report"
    
    def test_sidebar_strategy_dropdown_options(self):
        """Test that strategy dropdown has all expected options."""
        sidebar = create_sidebar()
        
        # Find strategy dropdown
        strategy_dropdown = None
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'id') and grandchild.id == "strategy-selector":
                        strategy_dropdown = grandchild
                        break
                if strategy_dropdown:
                    break
        
        assert strategy_dropdown is not None
        
        # Check options
        expected_options = [
            {'label': 'Greedy', 'value': SchedulerStrategy.GREEDY.value},
            {'label': 'Backtracking', 'value': SchedulerStrategy.BACKTRACKING.value},
            {'label': 'Heuristic', 'value': SchedulerStrategy.HEURISTIC.value},
            {'label': 'Lookahead', 'value': SchedulerStrategy.LOOKAHEAD.value},
            {'label': 'Random', 'value': SchedulerStrategy.RANDOM.value},
            {'label': 'Stochastic', 'value': SchedulerStrategy.STOCHASTIC.value},
            {'label': 'Optimal', 'value': SchedulerStrategy.OPTIMAL.value}
        ]
        
        assert strategy_dropdown.options == expected_options
    
    def test_sidebar_slider_marks(self):
        """Test that sliders have correct marks."""
        sidebar = create_sidebar()
        
        # Find sliders
        sliders = []
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "control-group":
                        for great_grandchild in grandchild.children:
                            if isinstance(great_grandchild, dcc.Slider):
                                sliders.append(great_grandchild)
        
        assert len(sliders) == 3
        
        # Check max concurrent slider marks
        max_concurrent_slider = sliders[0]
        expected_marks = {i: str(i) for i in range(1, 6)}
        assert max_concurrent_slider.marks == expected_marks
        
        # Check paper lead time slider marks
        paper_lead_slider = sliders[1]
        expected_marks = {i: str(i) for i in range(1, 7)}
        assert paper_lead_slider.marks == expected_marks
        
        # Check abstract lead time slider marks
        abstract_lead_slider = sliders[2]
        expected_marks = {0: '0', 15: '15', 30: '30', 45: '45', 60: '60'}
        assert abstract_lead_slider.marks == expected_marks
    
    def test_sidebar_checklist_options(self):
        """Test that checklists have correct options."""
        sidebar = create_sidebar()
        
        # Find checklists
        checklists = []
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and grandchild.className == "control-group":
                        for great_grandchild in grandchild.children:
                            if isinstance(great_grandchild, dcc.Checklist):
                                checklists.append(great_grandchild)
        
        assert len(checklists) == 3
        
        # Check blackout dates checklist
        blackout_checklist = checklists[0]
        expected_options = [{'label': 'Enable Blackout Dates', 'value': 'enabled'}]
        assert blackout_checklist.options == expected_options
        assert blackout_checklist.value == ['enabled']
        
        # Check dependencies checklist
        deps_checklist = checklists[1]
        expected_options = [{'label': 'Respect Dependencies', 'value': 'enabled'}]
        assert deps_checklist.options == expected_options
        assert deps_checklist.value == ['enabled']
        
        # Check engineering priority checklist
        eng_checklist = checklists[2]
        expected_options = [{'label': 'Prioritize Engineering', 'value': 'enabled'}]
        assert eng_checklist.options == expected_options
        assert eng_checklist.value == []
    
    def test_sidebar_button_ids_are_unique(self):
        """Test that sidebar buttons have unique IDs."""
        sidebar = create_sidebar()
        
        # Collect all button IDs
        button_ids = []
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'id') and grandchild.id:
                        button_ids.append(grandchild.id)
                    elif hasattr(grandchild, 'className') and 'control-group' in grandchild.className:
                        for great_grandchild in grandchild.children:
                            if hasattr(great_grandchild, 'id') and great_grandchild.id:
                                button_ids.append(great_grandchild.id)
        
        # Check that IDs are unique
        assert len(button_ids) == len(set(button_ids))
        
        # Check specific button IDs
        expected_ids = [
            "generate-schedule-btn",
            "save-schedule-btn", 
            "load-schedule-btn",
            "export-schedule-btn",
            "print-report-btn"
        ]
        for expected_id in expected_ids:
            assert expected_id in button_ids
    
    def test_sidebar_component_ids_are_unique(self):
        """Test that all sidebar components have unique IDs."""
        sidebar = create_sidebar()
        
        # Collect all component IDs
        component_ids = []
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'id') and grandchild.id:
                        component_ids.append(grandchild.id)
                    elif hasattr(grandchild, 'className') and 'control-group' in grandchild.className:
                        for great_grandchild in grandchild.children:
                            if hasattr(great_grandchild, 'id') and great_grandchild.id:
                                component_ids.append(great_grandchild.id)
        
        # Check that IDs are unique
        assert len(component_ids) == len(set(component_ids))
        
        # Check specific component IDs
        expected_ids = [
            "strategy-selector",
            "generate-schedule-btn",
            "max-concurrent-slider",
            "paper-lead-time-slider", 
            "abstract-lead-time-slider",
            "enable-blackout-dates",
            "enable-dependencies",
            "enable-engineering-priority",
            "save-schedule-btn",
            "load-schedule-btn",
            "export-schedule-btn",
            "print-report-btn"
        ]
        for expected_id in expected_ids:
            assert expected_id in component_ids
    
    def test_sidebar_has_correct_css_classes(self):
        """Test that sidebar and its components have correct CSS classes."""
        sidebar = create_sidebar()
        
        # Main sidebar class
        assert sidebar.className == "sidebar"
        
        # Check all sections have sidebar-section class
        for child in sidebar.children:
            assert child.className == "sidebar-section"
            
            # Check section titles have sidebar-section-title class
            section_title = child.children[0]
            assert section_title.className == "sidebar-section-title"
            
            # Check control groups have control-group class
            for grandchild in child.children[1:]:
                if hasattr(grandchild, 'className') and 'control-group' in grandchild.className:
                    assert grandchild.className == "control-group"
                elif hasattr(grandchild, 'className') and 'btn' in grandchild.className:
                    assert 'btn' in grandchild.className
                    assert 'btn-full' in grandchild.className
    
    def test_sidebar_icon_classes_are_valid(self):
        """Test that sidebar icons use valid FontAwesome classes."""
        sidebar = create_sidebar()
        
        # Check button icons
        expected_icons = [
            "fas fa-play",      # Generate Schedule
            "fas fa-save",      # Save Schedule
            "fas fa-folder-open", # Load Schedule
            "fas fa-download",  # Export CSV
            "fas fa-print"      # Print Report
        ]
        
        icon_index = 0
        for child in sidebar.children:
            if hasattr(child, 'className') and child.className == "sidebar-section":
                for grandchild in child.children:
                    if hasattr(grandchild, 'className') and 'btn' in grandchild.className:
                        icon = grandchild.children[0]
                        assert icon.className == expected_icons[icon_index]
                        icon_index += 1
