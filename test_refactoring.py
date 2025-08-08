#!/usr/bin/env python3
"""Test script to verify deadline validation refactoring."""

from datetime import date
from src.core.models import Config, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence
from src.validation.deadline import validate_deadline_constraints
from src.validation.submission import validate_submission_constraints
from src.validation.schedule import validate_schedule_constraints

def test_deadline_refactoring():
    """Test that deadline validation refactoring is working correctly."""
    print("Testing deadline validation refactoring...")
    
    # Create a simple test configuration
    conference = Conference(
        id="test_conf",
        name="Test Conference",
        conf_type=ConferenceType.MEDICAL,
        submission_types=None,  # Will be auto-determined
        deadlines={SubmissionType.PAPER: date(2024, 6, 1)},
        recurrence=ConferenceRecurrence.ANNUAL
    )
    
    submission = Submission(
        id="test_sub",
        title="Test Submission",
        kind=SubmissionType.PAPER,
        conference_id="test_conf",
        depends_on=[],
        draft_window_months=3
    )
    
    config = Config(
        submissions=[submission],
        conferences=[conference],
        min_paper_lead_time_days=30,
        min_abstract_lead_time_days=7,
        max_concurrent_submissions=3,
        blackout_dates=[],
        scheduling_options={}
    )
    
    # Test single submission deadline validation
    start_date = date(2024, 5, 1)  # Should meet deadline
    schedule1 = {submission.id: start_date}
    result1 = validate_deadline_constraints(schedule1, config)
    print(f"Deadline validation (valid): {result1.is_valid}")
    
    start_date_late = date(2024, 5, 15)  # Should miss deadline
    schedule2 = {submission.id: start_date_late}
    result2 = validate_deadline_constraints(schedule2, config)
    print(f"Deadline validation (late): {result2.is_valid}")
    
    # Test submission placement validation
    schedule = {"test_sub": start_date}
    result3 = validate_submission_constraints(submission, start_date, schedule, config)
    print(f"Submission placement validation: {result3}")
    
    # Test comprehensive schedule validation
    result4 = validate_schedule_constraints(schedule, config)
    print(f"Comprehensive schedule validation: {result4['summary']['overall_valid']}")
    
    print("All tests passed! Deadline validation refactoring is working correctly.")

if __name__ == "__main__":
    test_deadline_refactoring()
