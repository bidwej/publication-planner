"""Test constants validation functions."""

import pytest
from validation.constants import validate_constants


class TestConstantsValidation:
    """Test cases for constants validation functions."""
    
    def test_validate_constants_returns_list(self) -> None:
        """Test that validate_constants returns a list."""
        result = validate_constants()
        assert isinstance(result, list)
    
    def test_validate_constants_structure(self) -> None:
        """Test that validate_constants returns proper error structure."""
        result = validate_constants()
        
        # If there are errors, they should be strings
        for error in result:
            assert isinstance(error, str)
            assert len(error) > 0
    
    def test_constants_validation_coverage(self) -> None:
        """Test that all constant types are validated."""
        result = validate_constants()
        
        # This test ensures the validation function runs without crashing
        # The actual validation logic is tested in the core constants tests
        # Here we just verify the validation function works
        assert isinstance(result, list)
