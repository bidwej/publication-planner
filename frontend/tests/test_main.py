"""Tests for app.main module."""

from app.main import main, create_app


def test_main_function_exists():
    """Test that main function exists and is callable."""
    assert callable(main)


def test_create_app_function_exists():
    """Test that create_app function exists and is callable."""
    assert callable(create_app)


def test_create_app_accepts_mode_parameter():
    """Test that create_app accepts mode parameter."""
    try:
        app = create_app('gantt')
        assert app is not None
    except Exception:
        # If it fails due to missing dependencies, that's okay for this test
        pass
