"""Tests for quality scoring."""

from datetime import date

from src.scoring.quality import calculate_quality_score, calculate_quality_robustness, calculate_quality_balance


class TestCalculateQualityScore:
    """Test the calculate_quality_score function."""
    
    def test_empty_schedule(self, config):
        """Test quality calculation with empty schedule."""
        schedule = {}
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_single_submission(self, config):
        """Test quality calculation with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_multiple_submissions(self, config):
        """Test quality calculation with multiple submissions."""
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15),
            "test-abs": date(2025, 2, 1)
        }
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_diversity_score(self, config):
        """Test quality score for diverse submissions."""
        # Create a schedule with different types of submissions
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 1),
            "abstract1": date(2025, 3, 1),
            "mod1": date(2025, 4, 1)
        }
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_balance_score(self, config):
        """Test quality score for balanced schedule."""
        # Create a schedule with good spacing
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 3, 1),
            "paper3": date(2025, 5, 1),
            "paper4": date(2025, 7, 1)
        }
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_priority_weighting(self, config):
        """Test quality score with priority weighting."""
        schedule = {
            "high-priority": date(2025, 1, 1),
            "medium-priority": date(2025, 2, 1),
            "low-priority": date(2025, 3, 1)
        }
        score = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0


class TestQualityFunctions:
    """Test the quality calculation functions."""
    
    def test_calculate_schedule_robustness(self, config):
        """Test schedule robustness calculation."""
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        robustness = calculate_quality_robustness(schedule, config)
        assert isinstance(robustness, float)
        assert 0 <= robustness <= 100
    
    def test_calculate_quality_balance(self, config):
        """Test quality balance calculation."""
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        
        balance = calculate_quality_balance(schedule, config)
        assert isinstance(balance, float)
        assert 0 <= balance <= 100
    
    def test_robustness_with_empty_schedule(self, config):
        """Test robustness calculation with empty schedule."""
        schedule = {}
        robustness = calculate_quality_robustness(schedule, config)
        assert robustness == 0.0
    
    def test_balance_with_empty_schedule(self, config):
        """Test balance calculation with empty schedule."""
        schedule = {}
        balance = calculate_quality_balance(schedule, config)
        assert balance == 0.0
    
    def test_robustness_with_single_submission(self, config):
        """Test robustness calculation with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        robustness = calculate_quality_robustness(schedule, config)
        assert robustness == 100.0  # Single submission is always robust
    
    def test_balance_with_well_distributed_schedule(self, config):
        """Test balance calculation with well-distributed schedule."""
        schedule = {
            "jan-pap": date(2025, 1, 1),
            "mar-pap": date(2025, 3, 1),
            "jun-pap": date(2025, 6, 1),
            "sep-pap": date(2025, 9, 1)
        }
        
        balance = calculate_quality_balance(schedule, config)
        assert isinstance(balance, float)
        assert 0 <= balance <= 100
