"""Tests for scoring base module."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from scoring.base import (
    BaseScorer,
    PenaltyScorer,
    QualityScorer,
    EfficiencyScorer
)
from core.models import Config, Submission, Conference


class TestBaseScorer:
    """Test the base scorer class."""
    
    def test_base_scorer_initialization(self, config):
        """Test base scorer initialization."""
        # Can't instantiate abstract class directly
        with pytest.raises(TypeError):
            scorer = BaseScorer(config)
    
    def test_base_scorer_abstract_methods(self, config):
        """Test that base scorer has abstract methods."""
        # Can't instantiate abstract class directly
        with pytest.raises(TypeError):
            scorer = BaseScorer(config)


class TestPenaltyScorer:
    """Test the penalty scorer class."""
    
    def test_penalty_scorer_initialization(self, config):
        """Test penalty scorer initialization."""
        scorer = PenaltyScorer(config)
        assert scorer.config == config
    
    def test_calculate_penalty_score(self, config):
        """Test penalty score calculation."""
        scorer = PenaltyScorer(config)
        
        # Test with empty schedule
        schedule = {}
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_calculate_penalty_score_with_schedule(self, config):
        """Test penalty score calculation with actual schedule."""
        scorer = PenaltyScorer(config)
        
        # Create a simple schedule
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_get_penalty_breakdown(self, config):
        """Test penalty breakdown calculation."""
        scorer = PenaltyScorer(config)
        
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        breakdown = scorer.get_score_breakdown(schedule)
        assert isinstance(breakdown, dict)
        assert "total_penalty" in breakdown
        assert breakdown["total_penalty"] >= 0


class TestQualityScorer:
    """Test the quality scorer class."""
    
    def test_quality_scorer_initialization(self, config):
        """Test quality scorer initialization."""
        scorer = QualityScorer(config)
        assert scorer.config == config
    
    def test_calculate_quality_score(self, config):
        """Test quality score calculation."""
        scorer = QualityScorer(config)
        
        # Test with empty schedule
        schedule = {}
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_calculate_quality_score_with_schedule(self, config):
        """Test quality score calculation with actual schedule."""
        scorer = QualityScorer(config)
        
        # Create a simple schedule
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_get_quality_breakdown(self, config):
        """Test quality breakdown calculation."""
        scorer = QualityScorer(config)
        
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        breakdown = scorer.get_score_breakdown(schedule)
        assert isinstance(breakdown, dict)
        assert "quality_score" in breakdown
        assert breakdown["quality_score"] >= 0


class TestEfficiencyScorer:
    """Test the efficiency scorer class."""
    
    def test_efficiency_scorer_initialization(self, config):
        """Test efficiency scorer initialization."""
        scorer = EfficiencyScorer(config)
        assert scorer.config == config
    
    def test_calculate_efficiency_score(self, config):
        """Test efficiency score calculation."""
        scorer = EfficiencyScorer(config)
        
        # Test with empty schedule
        schedule = {}
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_calculate_efficiency_score_with_schedule(self, config):
        """Test efficiency score calculation with actual schedule."""
        scorer = EfficiencyScorer(config)
        
        # Create a simple schedule
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        score = scorer.calculate_score(schedule)
        assert isinstance(score, float)
        assert score >= 0
    
    def test_get_efficiency_breakdown(self, config):
        """Test efficiency breakdown calculation."""
        scorer = EfficiencyScorer(config)
        
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        breakdown = scorer.get_score_breakdown(schedule)
        assert isinstance(breakdown, dict)
        assert "efficiency_score" in breakdown
        assert breakdown["efficiency_score"] >= 0



