import json
import pytest
from unittest.mock import patch, mock_open
from validate_report import main


def test_missing_file(capsys):
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: testing_report.json not found" in captured.out


def test_invalid_json(capsys):
    mock_file_content = "invalid json{"
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Invalid JSON" in captured.out


def test_root_not_array(capsys):
    mock_file_content = json.dumps({"key": "value"})
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Root must be a JSON array" in captured.out


def test_valid_json_array(capsys):
    mock_file_content = json.dumps([{"id": 1}, {"id": 2}])
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        try:
            main()
        except SystemExit:
            pytest.fail("main() raised SystemExit unexpectedly on valid input")

    captured = capsys.readouterr()
    assert "Error" not in captured.out
