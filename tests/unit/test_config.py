import pytest
from unittest.mock import patch
from app.config import get_required_environ

def test_get_required_environ_success():
    """Test that it returns the value when the env var exists."""
    with patch.dict('os.environ', {'TEST_VAR': 'hello'}):
        assert get_required_environ('TEST_VAR') == 'hello'

def test_get_required_environ_missing():
    """Test that it raises KeyError when the env var is missing."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(KeyError):
            get_required_environ('MISSING_VAR')

def test_get_required_environ_empty():
    """Test that it raises ValueError when the env var is just whitespace."""
    with patch.dict('os.environ', {'EMPTY_VAR': '   '}):
        with pytest.raises(ValueError, match="cannot be empty"):
            get_required_environ('EMPTY_VAR')