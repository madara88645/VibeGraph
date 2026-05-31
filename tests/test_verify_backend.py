import sys
import os
from unittest.mock import patch, MagicMock

# Mock requests before importing verify_backend to prevent ModuleNotFoundError in CI
sys.modules["requests"] = MagicMock()

# Add the parent directory to sys.path so we can import verify_backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import verify_backend


@patch("verify_backend.requests.get")
def test_health_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_resp

    assert verify_backend.test_health() is True


@patch("verify_backend.requests.get")
def test_health_failure_status(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_resp.json.return_value = {"status": "error"}
    mock_get.return_value = mock_resp

    assert verify_backend.test_health() is False


@patch("verify_backend.requests.get")
def test_health_exception(mock_get):
    mock_get.side_effect = Exception("Connection refused")

    assert verify_backend.test_health() is False


@patch("verify_backend.requests.post")
def test_explain_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"explanation": "test", "snippet": "test"}
    mock_post.return_value = mock_resp

    assert verify_backend.test_explain() is True


@patch("verify_backend.requests.post")
def test_explain_failure_status(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Request"
    mock_post.return_value = mock_resp

    assert verify_backend.test_explain() is False


@patch("verify_backend.requests.post")
def test_explain_missing_keys(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"explanation": "test"}
    mock_post.return_value = mock_resp

    assert verify_backend.test_explain() is False


@patch("verify_backend.requests.post")
def test_explain_exception(mock_post):
    mock_post.side_effect = Exception("Connection refused")

    assert verify_backend.test_explain() is False
