"""Base classes for scoring strategies.

NOTE: This module provides a registry pattern for scoring strategies but is currently
not being used in the main application. It's kept for potential future use when
we want to make scoring strategies more configurable and extensible.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import date
from core.models import Config


class BaseScorer(ABC):
    """Abstract base class for all scoring strategies."""
    
    def __init__(self, config: Config):
        self.config = config
    
    @abstractmethod
    def calculate_score(self, schedule: Dict[str, date]) -> float:
        """Calculate a score for the given schedule."""
    
    @abstractmethod
    def get_score_breakdown(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Get detailed breakdown of the score calculation."""


class PenaltyScorer(BaseScorer):
    """Penalty-based scoring strategy."""
    
    def calculate_score(self, schedule: Dict[str, date]) -> float:
        """Calculate penalty score (lower is better)."""
        from scoring.penalty import calculate_penalty_score
        penalty_breakdown = calculate_penalty_score(schedule, self.config)
        return penalty_breakdown.total_penalty
    
    def get_score_breakdown(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Get detailed penalty breakdown."""
        from scoring.penalty import calculate_penalty_score
        penalty_breakdown = calculate_penalty_score(schedule, self.config)
        return {
            "total_penalty": penalty_breakdown.total_penalty,
            "deadline_penalties": penalty_breakdown.deadline_penalties,
            "dependency_penalties": penalty_breakdown.dependency_penalties,
            "resource_penalties": penalty_breakdown.resource_penalties
        }


class QualityScorer(BaseScorer):
    """Quality-based scoring strategy."""
    
    def calculate_score(self, schedule: Dict[str, date]) -> float:
        """Calculate quality score (higher is better)."""
        from scoring.quality import calculate_quality_score
        return calculate_quality_score(schedule, self.config)
    
    def get_score_breakdown(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Get detailed quality breakdown."""
        from scoring.quality import calculate_quality_score
        quality_score = calculate_quality_score(schedule, self.config)
        return {
            "quality_score": quality_score,
            "robustness": quality_score * 0.4,  # Simplified breakdown
            "balance": quality_score * 0.3,
            "compliance": quality_score * 0.3
        }


class EfficiencyScorer(BaseScorer):
    """Efficiency-based scoring strategy."""
    
    def calculate_score(self, schedule: Dict[str, date]) -> float:
        """Calculate efficiency score (higher is better)."""
        from scoring.efficiency import calculate_efficiency_score
        return calculate_efficiency_score(schedule, self.config)
    
    def get_score_breakdown(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Get detailed efficiency breakdown."""
        from .efficiency import calculate_efficiency_score, calculate_resource_efficiency, calculate_timeline_efficiency
        efficiency_score = calculate_efficiency_score(schedule, self.config)
        resource_metrics = calculate_resource_efficiency(schedule, self.config)
        timeline_metrics = calculate_timeline_efficiency(schedule, self.config)
        
        return {
            "efficiency_score": efficiency_score,
            "resource_efficiency": resource_metrics.utilization_rate,
            "timeline_efficiency": timeline_metrics.timeline_efficiency,
            "resource_metrics": resource_metrics,
            "timeline_metrics": timeline_metrics
        }


class CompositeScorer(BaseScorer):
    """Composite scoring strategy that combines multiple scorers."""
    
    def __init__(self, config: Config, weights: Dict[str, float] = None):
        super().__init__(config)
        self.weights = weights or {
            "penalty": 0.4,
            "quality": 0.3,
            "efficiency": 0.3
        }
        self.scorers = {
            "penalty": PenaltyScorer(config),
            "quality": QualityScorer(config),
            "efficiency": EfficiencyScorer(config)
        }
    
    def calculate_score(self, schedule: Dict[str, date]) -> float:
        """Calculate composite score."""
        scores = {}
        for name, scorer in self.scorers.items():
            if name == "penalty":
                # Invert penalty score (lower penalty = higher score)
                penalty_score = scorer.calculate_score(schedule)
                scores[name] = max(0, 100 - penalty_score / 10)  # Normalize to 0-100
            else:
                scores[name] = scorer.calculate_score(schedule) * 100  # Scale to 0-100
        
        # Weighted average
        composite_score = sum(
            scores[name] * self.weights[name] 
            for name in self.weights.keys()
        )
        
        return composite_score / 100  # Return as 0-1 score
    
    def get_score_breakdown(self, schedule: Dict[str, date]) -> Dict[str, Any]:
        """Get detailed composite breakdown."""
        breakdown = {
            "composite_score": self.calculate_score(schedule),
            "weights": self.weights,
            "component_scores": {}
        }
        
        for name, scorer in self.scorers.items():
            breakdown["component_scores"][name] = scorer.get_score_breakdown(schedule)
        
        return breakdown


# Registry pattern for scoring strategies
_scorers = {}


def register_scorer(name: str):
    """Decorator to register a scoring strategy."""
    def decorator(scorer_class):
        _scorers[name] = scorer_class
        return scorer_class
    return decorator


def create_scorer(name: str, config: Config) -> BaseScorer:
    """Create a scorer by name."""
    if name not in _scorers:
        raise ValueError(f"Unknown scorer: {name}. Available: {list(_scorers.keys())}")
    
    return _scorers[name](config)


def get_available_scorers() -> list[str]:
    """Get list of available scorer names."""
    return list(_scorers.keys())


# Register default scorers
register_scorer("penalty")(PenaltyScorer)
register_scorer("quality")(QualityScorer)
register_scorer("efficiency")(EfficiencyScorer)
register_scorer("composite")(CompositeScorer) 