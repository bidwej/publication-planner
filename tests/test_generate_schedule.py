"""Tests for the generate_schedule.py script."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

# Add root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generate_schedule import (
    compare_all_strategies,
    generate_schedule,
    create_parser,
    main
)
from core.models import SchedulerStrategy, Config


class TestGenerateSchedule:
    """Test the generate_schedule.py script functionality."""
    
    def test_generate_schedule_success(self):
        """Test generate_schedule with successful generation."""
        config = MagicMock(spec=Config)
        strategy = SchedulerStrategy.GREEDY
        
        # Mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.schedule.return_value = {"paper1-pap": date(2025, 1, 15)}
        
        with patch('generate_schedule.BaseScheduler.create_scheduler', return_value=mock_scheduler):
            with patch('generate_schedule.print_schedule_analysis') as mock_analyze:
                result = generate_schedule(config, strategy, verbose=True)
                
                # Should return the schedule
                assert result == {"paper1-pap": date(2025, 1, 15)}
                
                # Should call print_schedule_analysis
                mock_analyze.assert_called_once()
    
    def test_generate_schedule_failure(self):
        """Test generate_schedule with scheduler failure."""
        config = MagicMock(spec=Config)
        strategy = SchedulerStrategy.GREEDY
        
        with patch('generate_schedule.BaseScheduler.create_scheduler', side_effect=Exception("Scheduler failed")):
            with patch('builtins.print') as mock_print:
                result = generate_schedule(config, strategy, verbose=True)
                
                # Should return empty dict on failure
                assert result == {}
                
                # Should print error message
                mock_print.assert_called()
    
    def test_compare_all_strategies(self):
        """Test compare_all_strategies function."""
        config = MagicMock(spec=Config)
        
        # Mock successful schedule generation for all strategies
        mock_schedule = {"paper1-pap": date(2025, 1, 15)}
        
        with patch('generate_schedule.generate_schedule', return_value=mock_schedule):
            with patch('generate_schedule.print_strategy_comparison') as mock_compare:
                compare_all_strategies(config)
                
                # Should call print_strategy_comparison
                mock_compare.assert_called_once()
    
    def test_compare_all_strategies_with_output_file(self):
        """Test compare_all_strategies function with output file."""
        config = MagicMock(spec=Config)
        
        # Mock successful schedule generation for all strategies
        mock_schedule = {"paper1-pap": date(2025, 1, 15)}
        
        with patch('generate_schedule.generate_schedule', return_value=mock_schedule):
            with patch('generate_schedule.print_strategy_comparison') as mock_compare:
                compare_all_strategies(config, "test_output.json")
                
                # Should call print_strategy_comparison with output file
                mock_compare.assert_called_once()
                args, kwargs = mock_compare.call_args
                assert args[2] == "test_output.json"  # output_file parameter
    
    def test_create_parser(self):
        """Test create_parser function."""
        parser = create_parser()
        
        # Should have expected arguments
        assert parser is not None
        # Check that help argument exists
        assert any(arg.dest == 'list_strategies' for arg in parser._actions)
    
    def test_main_with_strategy_argument(self):
        """Test main function with strategy argument."""
        config = MagicMock(spec=Config)
        
        with patch('generate_schedule.load_config', return_value=config):
            with patch('generate_schedule.generate_schedule') as mock_generate:
                with patch('sys.argv', ['generate_schedule.py', '--strategy', 'greedy']):
                    main()
                    
                    # Should call generate_schedule with GREEDY strategy
                    mock_generate.assert_called_once()
                    args, kwargs = mock_generate.call_args
                    assert args[1] == SchedulerStrategy.GREEDY
    
    def test_main_with_invalid_strategy(self):
        """Test main function with invalid strategy argument."""
        config = MagicMock(spec=Config)
        
        with patch('generate_schedule.load_config', return_value=config):
            with patch('builtins.print') as mock_print:
                with patch('sys.argv', ['generate_schedule.py', '--strategy', 'invalid_strategy']):
                    with patch('sys.exit') as mock_exit:
                        main()
                        
                        # Should print error and exit
                        mock_print.assert_called()
                        mock_exit.assert_called_with(1)
    
    def test_main_with_file_not_found(self):
        """Test main function when config file is not found."""
        with patch('generate_schedule.load_config', side_effect=FileNotFoundError("Config not found")):
            with patch('builtins.print') as mock_print:
                with patch('sys.argv', ['generate_schedule.py', '--strategy', 'greedy']):
                    with patch('sys.exit') as mock_exit:
                        main()
                        
                        # Should print error and exit
                        mock_print.assert_called()
                        mock_exit.assert_called_with(1)
    
    def test_main_with_compare_argument(self):
        """Test main function with compare argument."""
        config = MagicMock(spec=Config)
        
        with patch('generate_schedule.load_config', return_value=config):
            with patch('generate_schedule.compare_all_strategies') as mock_compare:
                with patch('sys.argv', ['generate_schedule.py', '--compare']):
                    main()
                    
                    # Should call compare_all_strategies
                    mock_compare.assert_called_once()
    
    def test_main_with_list_strategies_argument(self):
        """Test main function with list-strategies argument."""
        with patch('generate_schedule.print_available_strategies') as mock_list:
            with patch('sys.argv', ['generate_schedule.py', '--list-strategies']):
                main()
                
                # Should call print_available_strategies
                mock_list.assert_called_once()
    
    def test_main_with_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['generate_schedule.py']):
            with pytest.raises(SystemExit):
                main()
    
    def test_main_with_both_strategy_and_compare(self):
        """Test main function with both strategy and compare arguments."""
        with patch('sys.argv', ['generate_schedule.py', '--strategy', 'greedy', '--compare']):
            with patch('argparse.ArgumentParser.error') as mock_error:
                main()
                
                # Should call parser.error
                mock_error.assert_called()


class TestGenerateScheduleIntegration:
    """Integration tests for generate_schedule.py."""
    
    def test_generate_schedule_with_default_config(self):
        """Test generate_schedule with default configuration."""
        # This test uses the default config functionality we implemented
        with patch('generate_schedule.load_config') as mock_load:
            # Mock load_config to return default config
            from core.models import Config
            mock_config = Config.create_default()
            mock_load.return_value = mock_config
            
            with patch('generate_schedule.generate_schedule') as mock_generate:
                with patch('sys.argv', ['generate_schedule.py', '--strategy', 'greedy']):
                    main()
                    
                    # Should call generate_schedule
                    mock_generate.assert_called_once()
                    args, kwargs = mock_generate.call_args
                    assert args[1] == SchedulerStrategy.GREEDY
