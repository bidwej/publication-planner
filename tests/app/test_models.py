"""Tests for app.models module."""

from datetime import date
from app.models import ScheduleSummary


class TestScheduleSummary:
    """Test cases for ScheduleSummary model."""
    
    def test_schedule_summary_creation(self):
        """Test ScheduleSummary creation with all parameters."""
        summary = ScheduleSummary(
            total_submissions=5,
            schedule_span=120,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 5, 1),
            penalty_score=150.50,
            quality_score=0.85,
            efficiency_score=0.78,
            deadline_compliance=90.5,
            resource_utilization=0.75
        )
        
        assert summary.total_submissions == 5
        assert summary.schedule_span == 120
        assert summary.start_date == date(2024, 1, 1)
        assert summary.end_date == date(2024, 5, 1)
        assert summary.penalty_score == 150.50
        assert summary.quality_score == 0.85
        assert summary.efficiency_score == 0.78
        assert summary.deadline_compliance == 90.5
        assert summary.resource_utilization == 0.75
    
    def test_schedule_summary_default_values(self):
        """Test ScheduleSummary creation with default values."""
        summary = ScheduleSummary(
            total_submissions=3,
            schedule_span=90,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 4, 1)
        )
        
        assert summary.total_submissions == 3
        assert summary.schedule_span == 90
        assert summary.start_date == date(2024, 1, 1)
        assert summary.end_date == date(2024, 4, 1)
        assert summary.penalty_score == 0.0
        assert summary.quality_score == 0.0
        assert summary.efficiency_score == 0.0
        assert summary.deadline_compliance == 0.0
        assert summary.resource_utilization == 0.0
    
    def test_schedule_summary_to_dict(self):
        """Test ScheduleSummary to_dict method."""
        summary = ScheduleSummary(
            total_submissions=2,
            schedule_span=60,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 1),
            penalty_score=100.0,
            quality_score=0.9,
            efficiency_score=0.8,
            deadline_compliance=95.0,
            resource_utilization=0.85
        )
        
        result = summary.to_dict()
        
        expected = {
            'total_submissions': 2,
            'schedule_span': 60,
            'start_date': '2024-01-01',
            'end_date': '2024-03-01',
            'penalty_score': 100.0,
            'quality_score': 0.9,
            'efficiency_score': 0.8,
            'deadline_compliance': 95.0,
            'resource_utilization': 0.85
        }
        
        assert result == expected
    
    def test_schedule_summary_from_dict(self):
        """Test ScheduleSummary from_dict method."""
        data = {
            'total_submissions': 4,
            'schedule_span': 100,
            'start_date': '2024-02-01',
            'end_date': '2024-05-01',
            'penalty_score': 200.0,
            'quality_score': 0.95,
            'efficiency_score': 0.88,
            'deadline_compliance': 98.0,
            'resource_utilization': 0.92
        }
        
        summary = ScheduleSummary.from_dict(data)
        
        assert summary.total_submissions == 4
        assert summary.schedule_span == 100
        assert summary.start_date == date(2024, 2, 1)
        assert summary.end_date == date(2024, 5, 1)
        assert summary.penalty_score == 200.0
        assert summary.quality_score == 0.95
        assert summary.efficiency_score == 0.88
        assert summary.deadline_compliance == 98.0
        assert summary.resource_utilization == 0.92
    
    def test_schedule_summary_str_representation(self):
        """Test ScheduleSummary string representation."""
        summary = ScheduleSummary(
            total_submissions=1,
            schedule_span=30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 2, 1),
            penalty_score=50.0,
            quality_score=0.7,
            efficiency_score=0.6,
            deadline_compliance=85.0,
            resource_utilization=0.65
        )
        
        result = str(summary)
        
        assert "ScheduleSummary" in result
        assert "total_submissions=1" in result
        assert "schedule_span=30" in result
        assert "penalty_score=50.0" in result
