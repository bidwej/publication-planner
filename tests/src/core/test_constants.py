from typing import Dict, List, Any, Optional

"""
Tests for constants module.
"""

import pytest
from src.core.constants import *


class TestConstants:
    """Test cases for constants module."""
    
    def test_constants_are_defined(self) -> None:
        """Test that all expected constants are defined."""
        # Test that all expected constant modules are imported
        assert 'SCHEDULING_CONSTANTS' in globals()
        assert 'PENALTY_CONSTANTS' in globals()
        assert 'EFFICIENCY_CONSTANTS' in globals()
        
        # Test that the constant objects exist
        assert SCHEDULING_CONSTANTS is not None
        assert PENALTY_CONSTANTS is not None
        assert EFFICIENCY_CONSTANTS is not None
    
    def test_constants_have_correct_types(self) -> None:
        """Test that constants have the expected types."""
        # Test that constants are the expected type (should be dataclasses or similar)
        assert hasattr(SCHEDULING_CONSTANTS, 'days_per_month')
        assert hasattr(SCHEDULING_CONSTANTS, 'default_paper_lead_time_months')
        assert hasattr(SCHEDULING_CONSTANTS, 'work_item_duration_days')
        assert hasattr(SCHEDULING_CONSTANTS, 'conference_response_time_days')
        assert hasattr(SCHEDULING_CONSTANTS, 'backtrack_limit_days')
        
        assert hasattr(PENALTY_CONSTANTS, 'default_mod_penalty_per_day')
        assert hasattr(PENALTY_CONSTANTS, 'default_paper_penalty_per_day')
        
        assert hasattr(EFFICIENCY_CONSTANTS, 'randomness_factor')
        assert hasattr(EFFICIENCY_CONSTANTS, 'lookahead_bonus_increment')
    
    def test_constants_values(self) -> None:
        """Test that constants have the expected values."""
        # Test specific constant values from the actual constants file
        assert SCHEDULING_CONSTANTS.days_per_month == 30
        assert SCHEDULING_CONSTANTS.default_paper_lead_time_months == 3
        assert SCHEDULING_CONSTANTS.work_item_duration_days == 14
        assert SCHEDULING_CONSTANTS.conference_response_time_days == 90
        assert SCHEDULING_CONSTANTS.backtrack_limit_days == 30
        
        assert PENALTY_CONSTANTS.default_mod_penalty_per_day == 1000.0
        assert PENALTY_CONSTANTS.default_paper_penalty_per_day == 2000.0
        
        assert EFFICIENCY_CONSTANTS.randomness_factor == 0.1
        assert EFFICIENCY_CONSTANTS.lookahead_bonus_increment == 0.5
