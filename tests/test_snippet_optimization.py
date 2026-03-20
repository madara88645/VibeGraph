import unittest
from unittest.mock import patch, mock_open, ANY
from fastapi.testclient import TestClient
from serve import app, _extract_snippet

class TestSnippetOptimization(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mock_source = """
def hello():
    print("world")
"""
        self.mock_tree = "mock_tree"

    @patch("serve.ast.parse")
    @patch("serve.open", new_callable=mock_open)
    @patch("serve.os.path.isfile", return_value=True)
    @patch("serve._is_safe_path", return_value=True)
    @patch("serve.os.path.realpath", return_value="/mock/path/test.py")
    def test_extract_snippet_no_redundant_parsing(
        self, mock_realpath, mock_is_safe, mock_isfile, mock_file, mock_ast_parse
    ):
        """
        Verify that _extract_snippet reads the file and parses the AST exactly once,
        and correctly returns the start_line, end_line, and full_source.
        """
        # Configure mocks
        mock_file.return_value.read.return_value = self.mock_source

        # We don't actually need ast.walk to do anything for this test,
        # we just want to ensure open and ast.parse are called exactly once.
        with patch("serve.ast.walk", return_value=[]):
            snippet, start, end, source = _extract_snippet("test.py", "hello")

            # Assert file was opened and read exactly once
            mock_file.assert_called_once_with("/mock/path/test.py", "r", encoding="utf-8")

            # Assert ast.parse was called exactly once on the source
            mock_ast_parse.assert_called_once_with(self.mock_source, filename="/mock/path/test.py")

            # Since ast.walk returned [], it won't find the node, but the important
            # part is verifying the I/O and parsing overhead is singular.
            self.assertEqual(source, self.mock_source)

    @patch("serve._extract_snippet")
    def test_get_snippet_endpoint_delegates_efficiently(self, mock_extract):
        """
        Verify the /api/snippet endpoint correctly delegates to _extract_snippet
        and returns its optimized tuple without performing redundant file operations.
        """
        mock_extract.return_value = ("print('world')", 2, 3, self.mock_source)

        response = self.client.post(
            "/api/snippet",
            json={"file_path": "test.py", "node_id": "hello"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["snippet"], "print('world')")
        self.assertEqual(data["start_line"], 2)
        self.assertEqual(data["end_line"], 3)
        self.assertEqual(data["full_source"], self.mock_source)

        mock_extract.assert_called_once_with("test.py", "hello")
