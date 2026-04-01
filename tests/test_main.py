import os
import unittest
from unittest.mock import patch, MagicMock

import main


class TestMainStart(unittest.TestCase):
    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("uvicorn.run")
    @patch("webbrowser.open")
    @patch("main.argparse.ArgumentParser.parse_args")
    @patch("main.console.print")
    def test_start_npm_found(
        self,
        mock_print,
        mock_parse_args,
        mock_webbrowser,
        mock_uvicorn,
        mock_which,
        mock_subprocess,
    ):
        # Set up mocks
        mock_args = MagicMock()
        mock_args.command = "start"
        mock_args.target = "."
        mock_parse_args.return_value = mock_args

        # Mock shutil.which
        mock_which.return_value = "/usr/bin/npm"

        # We need to test the condition where `npm` is found in PATH.
        # Given it runs uvicorn.run, which is an infinite blocking loop,
        # we mocked it above so it just returns immediately instead of starting a server.

        # We also need to patch out os functions temporarily inside test
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
            patch("analyst.analyzer.CodeAnalyzer") as mock_analyzer,
            patch("analyst.exporter.GraphExporter"),
            patch("shutil.copy"),
            patch("os.makedirs"),
        ):
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = {"graph": MagicMock()}

            def mock_exists_side_effect(path):
                if path == "explorer/public":
                    return True
                if path == os.path.join("explorer", "dist"):
                    return False
                if path == os.path.join("explorer", "node_modules"):
                    return False
                return True

            mock_exists.side_effect = mock_exists_side_effect
            mock_listdir.return_value = []  # Empty dist_dir

            # Run
            main.main()

            # Verify
            npm_name = "npm.cmd" if os.name == "nt" else "npm"
            mock_which.assert_called_once_with(npm_name)

            # Verify subprocess.run was called with the absolute path
            expected_calls = [
                unittest.mock.call(
                    ["/usr/bin/npm", "install"], cwd="explorer", check=True
                ),
                unittest.mock.call(
                    ["/usr/bin/npm", "run", "build"], cwd="explorer", check=True
                ),
            ]
            mock_subprocess.assert_has_calls(expected_calls)
            mock_uvicorn.assert_called_once()
            mock_webbrowser.assert_called_once()

    @patch("subprocess.run")
    @patch("shutil.which")
    @patch("main.argparse.ArgumentParser.parse_args")
    @patch("main.console.print")
    def test_start_npm_not_found(
        self, mock_print, mock_parse_args, mock_which, mock_subprocess
    ):
        # Set up mocks
        mock_args = MagicMock()
        mock_args.command = "start"
        mock_args.target = "."
        mock_parse_args.return_value = mock_args

        # Mock shutil.which to return None
        mock_which.return_value = None

        with (
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
            patch("analyst.analyzer.CodeAnalyzer") as mock_analyzer,
            patch("analyst.exporter.GraphExporter"),
            patch("shutil.copy"),
            patch("os.makedirs"),
        ):
            mock_analyzer_instance = mock_analyzer.return_value
            mock_analyzer_instance.analyze_file.return_value = {"graph": MagicMock()}

            def mock_exists_side_effect(path):
                if path == "explorer/public":
                    return True
                if path == os.path.join("explorer", "dist"):
                    return False
                return True

            mock_exists.side_effect = mock_exists_side_effect
            mock_listdir.return_value = []

            # Run
            main.main()

            # Verify error printed and subprocess NOT called
            npm_name = "npm.cmd" if os.name == "nt" else "npm"
            mock_which.assert_called_once_with(npm_name)

            mock_print.assert_called_with(
                f"[bold red]Error:[/bold red] {npm_name} not found in PATH"
            )
            mock_subprocess.assert_not_called()


if __name__ == "__main__":
    unittest.main()
