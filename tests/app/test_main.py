"""Tests for app.main module."""

from unittest.mock import Mock, patch

from app.main import main, create_dashboard_app, create_timeline_app


class TestMain:
    """Test cases for main app functionality."""
    
    @patch('app.main.create_dashboard_app')
    @patch('app.main.create_timeline_app')
    def test_main_dashboard_mode(self, mock_create_timeline, mock_create_dashboard):
        """Test main function in dashboard mode."""
        mock_app = Mock()
        mock_create_dashboard.return_value = mock_app
        
        with patch('sys.argv', ['main.py', '--mode', 'dashboard']):
            main()
        
        mock_create_dashboard.assert_called_once()
        mock_app.run_server.assert_called_once()
        mock_create_timeline.assert_not_called()
    
    @patch('app.main.create_dashboard_app')
    @patch('app.main.create_timeline_app')
    def test_main_timeline_mode(self, mock_create_timeline, mock_create_dashboard):
        """Test main function in timeline mode."""
        mock_app = Mock()
        mock_create_timeline.return_value = mock_app
        
        with patch('sys.argv', ['main.py', '--mode', 'timeline', '--port', '8051']):
            main()
        
        mock_create_timeline.assert_called_once()
        mock_app.run_server.assert_called_once()
        mock_create_dashboard.assert_not_called()
    
    @patch('app.main.dash.Dash')
    @patch('app.main.create_layout')
    def test_create_dashboard_app(self, mock_create_layout, mock_dash):
        """Test dashboard app creation."""
        mock_app = Mock()
        mock_dash.return_value = mock_app
        mock_layout = Mock()
        mock_create_layout.return_value = mock_layout
        
        result = create_dashboard_app()
        
        mock_dash.assert_called_once()
        mock_create_layout.assert_called_once()
        assert result == mock_app
        assert mock_app.layout == mock_layout
    
    @patch('app.main.dash.Dash')
    @patch('app.main.create_timeline_layout')
    def test_create_timeline_app(self, mock_create_layout, mock_dash):
        """Test timeline app creation."""
        mock_app = Mock()
        mock_dash.return_value = mock_app
        mock_layout = Mock()
        mock_create_layout.return_value = mock_layout
        
        result = create_timeline_app()
        
        mock_dash.assert_called_once()
        mock_create_layout.assert_called_once()
        assert result == mock_app
        assert mock_app.layout == mock_layout
