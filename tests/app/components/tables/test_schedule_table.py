"""
Tests for schedule table component.
"""

import pytest
from datetime import date
from unittest.mock import Mock
import sys
import os

# Add the src directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from components.tables.schedule_table import (
    create_schedule_table,
    create_violations_table,
    create_metrics_table,
    create_analytics_table
)
from core.models import Config, Submission, SubmissionType, Conference


class TestScheduleTable:
    """Test schedule table functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        config = Mock(spec=Config)
        config.submissions_dict = {
            'sub1': Mock(spec=Submission, 
                        id='sub1', 
                        title='Test Paper 1',
                        kind=SubmissionType.PAPER,
                        engineering=True,
                        conference_id='conf1',
                        get_duration_days=lambda cfg: 30),
            'sub2': Mock(spec=Submission,
                        id='sub2',
                        title='Test Abstract 1',
                        kind=SubmissionType.ABSTRACT,
                        engineering=False,
                        conference_id='conf2',
                        get_duration_days=lambda cfg: 0),
            'sub3': Mock(spec=Submission,
                        id='sub3',
                        title='Test Paper 2',
                        kind=SubmissionType.PAPER,
                        engineering=False,
                        conference_id='conf1',
                        get_duration_days=lambda cfg: 45)
        }
        config.conferences_dict = {
            'conf1': Mock(spec=Conference, name='Conference A'),
            'conf2': Mock(spec=Conference, name='Conference B')
        }
        # Ensure the mock conferences have the name attribute properly set
        config.conferences_dict['conf1'].name = 'Conference A'
        config.conferences_dict['conf2'].name = 'Conference B'
        return config
    
    @pytest.fixture
    def sample_schedule(self):
        """Create a sample schedule for testing."""
        return {
            'sub1': date(2024, 1, 1),
            'sub2': date(2024, 2, 1),
            'sub3': date(2024, 3, 1)
        }
    
    def test_create_schedule_table_with_data(self, sample_config, sample_schedule):
        """Test creating schedule table with valid data."""
        table_data = create_schedule_table(sample_schedule, sample_config)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 3
        
        # Check first row structure
        first_row = table_data[0]
        expected_keys = ['id', 'title', 'type', 'start_date', 'end_date', 
                        'conference', 'status', 'duration', 'engineering']
        
        for key in expected_keys:
            assert key in first_row
        
        # Check data types and values
        assert first_row['id'] == 'sub1'
        assert first_row['title'] == 'Test Paper 1'
        assert first_row['type'] == 'Paper'
        assert first_row['start_date'] == '2024-01-01'
        assert first_row['end_date'] == '2024-01-31'  # start + 30 days
        assert first_row['conference'] == 'Conference A'
        assert first_row['duration'] == '30 days'
        assert first_row['engineering'] == 'Yes'
    
    def test_create_schedule_table_empty_schedule(self, sample_config):
        """Test creating schedule table with empty schedule."""
        table_data = create_schedule_table({}, sample_config)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_schedule_table_none_schedule(self, sample_config):
        """Test creating schedule table with None schedule."""
        table_data = create_schedule_table(None, sample_config)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_schedule_table_missing_submission(self, sample_config):
        """Test creating schedule table with missing submission in config."""
        schedule = {'sub1': date(2024, 1, 1), 'missing_sub': date(2024, 2, 1)}
        
        table_data = create_schedule_table(schedule, sample_config)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 1  # Only sub1 should be included
        assert table_data[0]['id'] == 'sub1'
    
    def test_create_schedule_table_abstract_submission(self, sample_config, sample_schedule):
        """Test creating schedule table with abstract submission."""
        table_data = create_schedule_table(sample_schedule, sample_config)
        
        # Find abstract submission
        abstract_row = next(row for row in table_data if row['id'] == 'sub2')
        
        assert abstract_row['type'] == 'Abstract'
        assert abstract_row['duration'] == '0 days'
        assert abstract_row['engineering'] == 'No'
        assert abstract_row['end_date'] == abstract_row['start_date']  # Same day for abstracts
    
    def test_create_schedule_table_sorting(self, sample_config):
        """Test that schedule table is sorted by start date."""
        schedule = {
            'sub3': date(2024, 3, 1),
            'sub1': date(2024, 1, 1),
            'sub2': date(2024, 2, 1)
        }
        
        table_data = create_schedule_table(schedule, sample_config)
        
        assert len(table_data) == 3
        assert table_data[0]['start_date'] == '2024-01-01'
        assert table_data[1]['start_date'] == '2024-02-01'
        assert table_data[2]['start_date'] == '2024-03-01'


class TestViolationsTable:
    """Test violations table functionality."""
    
    @pytest.fixture
    def sample_validation_result(self):
        """Create a sample validation result for testing."""
        return {
            'constraints': {
                'deadline_constraints': {
                    'violations': [
                        {
                            'submission_id': 'sub1',
                            'message': 'Deadline missed by 5 days',
                            'severity': 'high',
                            'impact': 'Major penalty'
                        }
                    ]
                },
                'dependency_constraints': {
                    'violations': [
                        {
                            'submission_id': 'sub2',
                            'message': 'Dependency not satisfied',
                            'severity': 'medium',
                            'impact': 'Schedule conflict'
                        }
                    ]
                }
            }
        }
    
    def test_create_violations_table_with_data(self, sample_validation_result):
        """Test creating violations table with valid data."""
        table_data = create_violations_table(sample_validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 2
        
        # Check first violation
        first_violation = table_data[0]
        expected_keys = ['type', 'submission', 'description', 'severity', 'impact']
        
        for key in expected_keys:
            assert key in first_violation
        
        assert first_violation['type'] == 'Deadline Constraints'
        assert first_violation['submission'] == 'sub1'
        assert 'Deadline missed' in first_violation['description']
        assert first_violation['severity'] == 'high'
    
    def test_create_violations_table_empty_result(self):
        """Test creating violations table with empty validation result."""
        table_data = create_violations_table({})
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_violations_table_none_result(self):
        """Test creating violations table with None validation result."""
        table_data = create_violations_table(None)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_violations_table_no_violations(self):
        """Test creating violations table with no violations."""
        validation_result = {
            'constraints': {
                'deadline_constraints': {
                    'violations': []
                }
            }
        }
        
        table_data = create_violations_table(validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_violations_table_missing_violations_key(self):
        """Test creating violations table with missing violations key."""
        validation_result = {
            'constraints': {
                'deadline_constraints': {
                    'some_other_key': []
                }
            }
        }
        
        table_data = create_violations_table(validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0


class TestMetricsTable:
    """Test metrics table functionality."""
    
    @pytest.fixture
    def sample_validation_result(self):
        """Create a sample validation result for testing."""
        return {
            'scores': {
                'penalty_score': 75.5,
                'quality_score': 82.3,
                'efficiency_score': 68.9
            },
            'summary': {
                'overall_score': 75.6
            }
        }
    
    def test_create_metrics_table_with_data(self, sample_validation_result):
        """Test creating metrics table with valid data."""
        table_data = create_metrics_table(sample_validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 4  # 4 metrics: penalty, quality, efficiency, overall
        
        # Check first metric
        first_metric = table_data[0]
        expected_keys = ['metric', 'value', 'status']
        
        for key in expected_keys:
            assert key in first_metric
        
        assert first_metric['metric'] == 'Penalty Score'
        assert first_metric['value'] == '75.5'
        assert first_metric['status'] == 'Good'  # 75.5 is in Good range
    
    def test_create_metrics_table_empty_result(self):
        """Test creating metrics table with empty validation result."""
        table_data = create_metrics_table({})
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_metrics_table_none_result(self):
        """Test creating metrics table with None validation result."""
        table_data = create_metrics_table(None)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_metrics_table_missing_scores(self):
        """Test creating metrics table with missing scores."""
        validation_result = {'summary': {'overall_score': 75.6}}
        
        table_data = create_metrics_table(validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 4  # Still creates all metrics with default values
        
        # Check that missing scores default to 0
        penalty_metric = next(m for m in table_data if m['metric'] == 'Penalty Score')
        assert penalty_metric['value'] == '0.0'
        assert penalty_metric['status'] == 'Poor'
    
    def test_create_metrics_table_score_status_ranges(self):
        """Test that score status is correctly assigned based on ranges."""
        test_cases = [
            (95.0, 'Excellent'),
            (85.0, 'Excellent'),
            (75.0, 'Good'),
            (65.0, 'Good'),
            (55.0, 'Fair'),
            (45.0, 'Fair'),
            (35.0, 'Poor'),
            (25.0, 'Poor')
        ]
        
        for score, expected_status in test_cases:
            validation_result = {
                'scores': {
                    'penalty_score': score,
                    'quality_score': score,
                    'efficiency_score': score
                },
                'summary': {
                    'overall_score': score
                }
            }
            
            table_data = create_metrics_table(validation_result)
            
            # Check that all metrics have the expected status
            for metric in table_data:
                assert metric['status'] == expected_status


class TestAnalyticsTable:
    """Test analytics table functionality."""
    
    @pytest.fixture
    def sample_validation_result(self):
        """Create a sample validation result for testing."""
        return {
            'summary': {
                'total_submissions': 5,
                'duration_days': 120,
                'deadline_compliance': 85.2,
                'dependency_satisfaction': 90.0,
                'total_violations': 3,
                'critical_violations': 1
            }
        }
    
    def test_create_analytics_table_with_data(self, sample_validation_result):
        """Test creating analytics table with valid data."""
        table_data = create_analytics_table(sample_validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 6  # 6 analytics categories
        
        # Check first analytics entry
        first_entry = table_data[0]
        expected_keys = ['category', 'metric', 'value']
        
        for key in expected_keys:
            assert key in first_entry
        
        assert first_entry['category'] == 'Submissions'
        assert first_entry['metric'] == 'Total Submissions'
        assert first_entry['value'] == '5'
    
    def test_create_analytics_table_empty_result(self):
        """Test creating analytics table with empty validation result."""
        table_data = create_analytics_table({})
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_analytics_table_none_result(self):
        """Test creating analytics table with None validation result."""
        table_data = create_analytics_table(None)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 0
    
    def test_create_analytics_table_missing_summary(self):
        """Test creating analytics table with missing summary."""
        validation_result = {'scores': {'penalty_score': 75.5}}
        
        table_data = create_analytics_table(validation_result)
        
        assert isinstance(table_data, list)
        assert len(table_data) == 6  # Still creates all analytics with default values
        
        # Check that missing values default to 0
        submissions_entry = next(e for e in table_data if e['metric'] == 'Total Submissions')
        assert submissions_entry['value'] == '0'
    
    def test_create_analytics_table_all_categories(self, sample_validation_result):
        """Test that all analytics categories are included."""
        table_data = create_analytics_table(sample_validation_result)
        
        categories = [entry['category'] for entry in table_data]
        expected_categories = ['Submissions', 'Timeline', 'Compliance', 'Dependencies', 'Violations', 'Violations']
        
        assert categories == expected_categories
        
        # Check specific metrics
        metrics = [entry['metric'] for entry in table_data]
        expected_metrics = [
            'Total Submissions',
            'Duration (days)',
            'Deadline Compliance',
            'Dependency Satisfaction',
            'Total Violations',
            'Critical Violations'
        ]
        
        assert metrics == expected_metrics


class TestTableIntegration:
    """Integration tests for table functionality."""
    
    def test_complete_table_workflow(self):
        """Test complete table generation workflow."""
        # Create realistic test data
        config = Mock(spec=Config)
        config.submissions_dict = {
            'paper1': Mock(spec=Submission,
                          id='paper1',
                          title='Research Paper',
                          kind=SubmissionType.PAPER,
                          engineering=True,
                          conference_id='conf1',
                          get_duration_days=lambda cfg: 60),
            'abstract1': Mock(spec=Submission,
                             id='abstract1',
                             title='Conference Abstract',
                             kind=SubmissionType.ABSTRACT,
                             engineering=False,
                             conference_id='conf2',
                             get_duration_days=lambda cfg: 0)
        }
        config.conferences_dict = {
            'conf1': Mock(spec=Conference, name='IEEE Conference'),
            'conf2': Mock(spec=Conference, name='ACM Conference')
        }
        # Ensure the mock conferences have the name attribute properly set
        config.conferences_dict['conf1'].name = 'IEEE Conference'
        config.conferences_dict['conf2'].name = 'ACM Conference'
        
        schedule = {
            'paper1': date(2024, 1, 1),
            'abstract1': date(2024, 2, 1)
        }
        
        validation_result = {
            'scores': {
                'penalty_score': 85.2,
                'quality_score': 90.1,
                'efficiency_score': 78.4
            },
            'summary': {
                'overall_score': 84.6,
                'total_submissions': 2,
                'duration_days': 60,
                'deadline_compliance': 95.0,
                'dependency_satisfaction': 100.0,
                'total_violations': 0,
                'critical_violations': 0
            },
            'constraints': {
                'deadline_constraints': {
                    'violations': []
                }
            }
        }
        
        # Test schedule table
        schedule_table = create_schedule_table(schedule, config)
        assert isinstance(schedule_table, list)
        assert len(schedule_table) == 2
        
        # Test violations table
        violations_table = create_violations_table(validation_result)
        assert isinstance(violations_table, list)
        assert len(violations_table) == 0  # No violations
        
        # Test metrics table
        metrics_table = create_metrics_table(validation_result)
        assert isinstance(metrics_table, list)
        assert len(metrics_table) == 4
        
        # Test analytics table
        analytics_table = create_analytics_table(validation_result)
        assert isinstance(analytics_table, list)
        assert len(analytics_table) == 6
    
    def test_table_edge_cases(self):
        """Test table edge cases."""
        config = Mock(spec=Config)
        config.submissions_dict = {}
        config.conferences_dict = {}
        
        # Test with various edge cases
        edge_cases = [
            {},  # Empty dict
            None,  # None
            {'scores': {}},  # Empty scores
            {'summary': {}},  # Empty summary
        ]
        
        for case in edge_cases:
            # Test all table functions with edge cases
            schedule_table = create_schedule_table({}, config)
            violations_table = create_violations_table(case)
            metrics_table = create_metrics_table(case)
            analytics_table = create_analytics_table(case)
            
            assert isinstance(schedule_table, list)
            assert isinstance(violations_table, list)
            assert isinstance(metrics_table, list)
            assert isinstance(analytics_table, list)
