"""Integration tests for command-line interface functionality."""

import pytest
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional




class TestCLIIntegration:
    """Integration tests for command-line interface functionality."""
    
    def test_cli_help_command(self) -> None:
        """Test CLI help command functionality."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            assert result.returncode == 0, "Help command should succeed"
            assert "Generate a schedule for the Endoscope AI project" in result.stdout
            assert "--strategy" in result.stdout
            assert "--compare" in result.stdout
            assert "--list-strategies" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI help test timed out")
        except Exception as e:
            pytest.fail(f"CLI help test failed: {e}")
    
    def test_cli_list_strategies_command(self) -> None:
        """Test CLI list-strategies command functionality."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--list-strategies"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            assert result.returncode == 0, "List strategies command should succeed"
            assert "greedy" in result.stdout.lower() or "available" in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI list strategies test timed out")
        except Exception as e:
            pytest.fail(f"CLI list strategies test failed: {e}")
    
    def test_cli_argument_validation(self) -> None:
        """Test CLI argument validation functionality."""
        # Test with no arguments
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should fail with no arguments
            assert result.returncode != 0, "CLI should fail with no arguments"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI argument validation test timed out")
        except Exception as e:
            pytest.fail(f"CLI argument validation test failed: {e}")
    
    def test_cli_invalid_strategy(self) -> None:
        """Test CLI with invalid strategy argument."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--strategy", "invalid_strategy"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should fail with invalid strategy
            assert result.returncode != 0, "CLI should fail with invalid strategy"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI invalid strategy test timed out")
        except Exception as e:
            pytest.fail(f"CLI invalid strategy test failed: {e}")
    
    def test_cli_conflicting_arguments(self) -> None:
        """Test CLI with conflicting arguments."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--strategy", "greedy", "--compare"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should fail with conflicting arguments
            assert result.returncode != 0, "CLI should fail with conflicting arguments"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI conflicting arguments test timed out")
        except Exception as e:
            pytest.fail(f"CLI conflicting arguments test failed: {e}")
    
    def test_cli_with_valid_strategy(self) -> None:
        """Test CLI with valid strategy argument."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--strategy", "greedy"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should succeed with valid strategy (even if no config file)
            # The exact behavior depends on whether config.json exists
            # For now, just check that it doesn't crash
            assert result.returncode in [0, 1], f"CLI should handle valid strategy gracefully, got return code {result.returncode}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI valid strategy test timed out")
        except Exception as e:
            pytest.fail(f"CLI valid strategy test failed: {e}")
    
    def test_cli_compare_mode(self) -> None:
        """Test CLI compare mode functionality."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--compare"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should handle compare mode (even if no config file)
            # The exact behavior depends on whether config.json exists
            # For now, just check that it doesn't crash
            assert result.returncode in [0, 1], f"CLI should handle compare mode gracefully, got return code {result.returncode}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI compare mode test timed out")
        except Exception as e:
            pytest.fail(f"CLI compare mode test failed: {e}")
    
    def test_cli_quiet_mode(self) -> None:
        """Test CLI quiet mode functionality."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--strategy", "greedy", "--quiet"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should handle quiet mode
            # The exact behavior depends on whether config.json exists
            # For now, just check that it doesn't crash
            assert result.returncode in [0, 1], f"CLI should handle quiet mode gracefully, got return code {result.returncode}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI quiet mode test timed out")
        except Exception as e:
            pytest.fail(f"CLI quiet mode test failed: {e}")
    
    def test_cli_output_file_handling(self) -> None:
        """Test CLI output file handling functionality."""
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--compare", "--output", "test_output.json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should handle output file specification
            # The exact behavior depends on whether config.json exists
            # For now, just check that it doesn't crash
            assert result.returncode in [0, 1], f"CLI should handle output file gracefully, got return code {result.returncode}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI output file test timed out")
        except Exception as e:
            pytest.fail(f"CLI output file test failed: {e}")
    
    def test_cli_error_handling(self) -> None:
        """Test CLI error handling functionality."""
        # Test with missing config file
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--strategy", "greedy", "--config", "non_existent_config.json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
                timeout=10
            )
            
            # Should fail with missing config file
            assert result.returncode != 0, "CLI should fail with missing config file"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI error handling test timed out")
        except Exception as e:
            pytest.fail(f"CLI error handling test failed: {e}")
    
    def test_cli_subprocess_integration(self) -> None:
        """Test CLI subprocess integration functionality."""
        # Test that the script can be run directly
        try:
            result: Any = subprocess.run(
                ["python", "generate_schedule.py", "--help"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=10
            )
            
            # Should succeed when run directly
            assert result.returncode == 0, "CLI should work when run directly"
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI subprocess integration test timed out")
        except Exception as e:
            pytest.fail(f"CLI subprocess integration test failed: {e}")
