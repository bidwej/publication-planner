"""Tests for app.layouts.header module."""

from dash import html
from app.layouts.header import create_header


class TestHeaderLayout:
    """Test cases for header layout component."""
    
    def test_create_header_returns_header_element(self):
        """Test that create_header returns a header element."""
        header = create_header()
        
        assert isinstance(header, html.Header)
        assert header.className == "app-header"
    
    def test_header_contains_brand_section(self):
        """Test that header contains the brand section with logo and title."""
        header = create_header()
        
        # Find the brand section
        brand_section = None
        for child in header.children:
            if hasattr(child, 'className') and child.className == "header-brand":
                brand_section = child
                break
        
        assert brand_section is not None
        assert isinstance(brand_section, html.Div)
        
        # Check brand section contents
        brand_children = brand_section.children
        assert len(brand_children) == 3
        
        # Check icon
        assert isinstance(brand_children[0], html.I)
        assert brand_children[0].className == "fas fa-calendar-alt header-icon"
        
        # Check title
        assert isinstance(brand_children[1], html.H1)
        assert brand_children[1].children == "Paper Planner"
        assert brand_children[1].className == "header-title"
        
        # Check subtitle
        assert isinstance(brand_children[2], html.Span)
        assert brand_children[2].children == "Academic Schedule Optimizer"
        assert brand_children[2].className == "header-subtitle"
    
    def test_header_contains_navigation_section(self):
        """Test that header contains the navigation section."""
        header = create_header()
        
        # Find the navigation section
        nav_section = None
        for child in header.children:
            if hasattr(child, 'className') and child.className == "header-nav":
                nav_section = child
                break
        
        assert nav_section is not None
        assert isinstance(nav_section, html.Nav)
        
        # Check navigation links
        nav_links = nav_section.children
        expected_links = ["Dashboard", "Analytics", "Settings", "Help"]
        
        assert len(nav_links) == len(expected_links)
        
        for i, link in enumerate(nav_links):
            assert isinstance(link, html.A)
            assert link.children == expected_links[i]
            assert link.className == "nav-link"
            assert link.href == "#"
            
            # First link should be active
            if i == 0:
                assert "active" in link.className
            else:
                assert "active" not in link.className
    
    def test_header_contains_actions_section(self):
        """Test that header contains the actions section with buttons."""
        header = create_header()
        
        # Find the actions section
        actions_section = None
        for child in header.children:
            if hasattr(child, 'className') and child.className == "header-actions":
                actions_section = child
                break
        
        assert actions_section is not None
        assert isinstance(actions_section, html.Div)
        
        # Check action buttons
        action_buttons = actions_section.children
        assert len(action_buttons) == 3
        
        # Check save button
        save_btn = action_buttons[0]
        assert isinstance(save_btn, html.Button)
        assert save_btn.id == "header-save-btn"
        assert save_btn.className == "btn btn-primary"
        assert len(save_btn.children) == 2
        assert isinstance(save_btn.children[0], html.I)
        assert save_btn.children[0].className == "fas fa-save"
        assert save_btn.children[1] == " Save"
        
        # Check load button
        load_btn = action_buttons[1]
        assert isinstance(load_btn, html.Button)
        assert load_btn.id == "header-load-btn"
        assert load_btn.className == "btn btn-secondary"
        assert len(load_btn.children) == 2
        assert isinstance(load_btn.children[0], html.I)
        assert load_btn.children[0].className == "fas fa-download"
        assert load_btn.children[1] == " Load"
        
        # Check settings button
        settings_btn = action_buttons[2]
        assert isinstance(settings_btn, html.Button)
        assert settings_btn.className == "btn btn-icon"
        assert settings_btn.title == "Settings"
        assert len(settings_btn.children) == 1
        assert isinstance(settings_btn.children[0], html.I)
        assert settings_btn.children[0].className == "fas fa-cog"
    
    def test_header_structure_completeness(self):
        """Test that header has all required sections in correct order."""
        header = create_header()
        
        # Check that header has exactly 3 main sections
        assert len(header.children) == 3
        
        # Check section order: brand, nav, actions
        sections = header.children
        assert sections[0].className == "header-brand"
        assert sections[1].className == "header-nav"
        assert sections[2].className == "header-actions"
    
    def test_header_has_correct_css_classes(self):
        """Test that header and its components have correct CSS classes."""
        header = create_header()
        
        # Main header class
        assert header.className == "app-header"
        
        # Check all sections have their classes
        sections = header.children
        assert sections[0].className == "header-brand"
        assert sections[1].className == "header-nav"
        assert sections[2].className == "header-actions"
        
        # Check navigation links have nav-link class
        nav_links = sections[1].children
        for link in nav_links:
            assert "nav-link" in link.className
        
        # Check buttons have btn classes
        action_buttons = sections[2].children
        for button in action_buttons:
            assert "btn" in button.className
    
    def test_header_button_ids_are_unique(self):
        """Test that header buttons have unique IDs."""
        header = create_header()
        
        action_buttons = header.children[2].children
        button_ids = []
        
        for button in action_buttons:
            if hasattr(button, 'id') and button.id:
                button_ids.append(button.id)
        
        # Check that IDs are unique
        assert len(button_ids) == len(set(button_ids))
        assert "header-save-btn" in button_ids
        assert "header-load-btn" in button_ids
    
    def test_header_icon_classes_are_valid(self):
        """Test that header icons use valid FontAwesome classes."""
        header = create_header()
        
        # Check brand icon
        brand_icon = header.children[0].children[0]
        assert brand_icon.className == "fas fa-calendar-alt header-icon"
        
        # Check action button icons
        action_buttons = header.children[2].children
        expected_icons = ["fas fa-save", "fas fa-download", "fas fa-cog"]
        
        for i, button in enumerate(action_buttons):
            icon = button.children[0]
            assert icon.className == expected_icons[i]
    
    def test_header_navigation_links_have_correct_structure(self):
        """Test that navigation links have correct href and structure."""
        header = create_header()
        
        nav_links = header.children[1].children
        
        for link in nav_links:
            assert link.href == "#"
            assert isinstance(link.children, str)
            assert len(link.children) > 0
            assert "nav-link" in link.className
    
    def test_header_is_accessible(self):
        """Test that header components have proper accessibility attributes."""
        header = create_header()
        
        # Check that buttons have proper titles where needed
        action_buttons = header.children[2].children
        
        # Settings button should have title
        settings_btn = action_buttons[2]
        assert settings_btn.title == "Settings"
        
        # Other buttons should have descriptive text
        save_btn = action_buttons[0]
        load_btn = action_buttons[1]
        assert "Save" in save_btn.children[1]
        assert "Load" in load_btn.children[1]
