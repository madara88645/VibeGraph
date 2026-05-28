import pytest
from unittest.mock import patch, MagicMock
import requests
import verify_backend

def test_health_success():
    with patch("verify_backend.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_resp

        result = verify_backend.test_health()
        assert result is True

def test_health_failure_status():
    with patch("verify_backend.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        result = verify_backend.test_health()
        assert result is False

def test_health_exception():
    with patch("verify_backend.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = verify_backend.test_health()
        assert result is False

def test_explain_success():
    with patch("verify_backend.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"explanation": "...", "snippet": "..."}
        mock_post.return_value = mock_resp

        result = verify_backend.test_explain()
        assert result is True

def test_explain_failure_keys():
    with patch("verify_backend.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"explanation": "..."} # missing snippet
        mock_post.return_value = mock_resp

        result = verify_backend.test_explain()
        assert result is False

def test_explain_failure_status():
    with patch("verify_backend.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_post.return_value = mock_resp

        result = verify_backend.test_explain()
        assert result is False

def test_explain_exception():
    with patch("verify_backend.requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        result = verify_backend.test_explain()
        assert result is False
