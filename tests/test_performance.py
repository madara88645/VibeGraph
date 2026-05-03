import os
import tempfile
import pytest
from unittest.mock import patch
from analyst.analyzer import CodeAnalyzer, _ast_cache_clear

@pytest.fixture(autouse=True)
def clear_caches():
    # Ensure caches are clean before each test
    _ast_cache_clear()
    yield
    _ast_cache_clear()

def test_graph_caching_big_o_performance():
    """
    Tests the performance regression protection by ensuring that 
    analyzing the same files twice does NOT invoke the AST parser
    or CallGraphVisitor a second time, guaranteeing O(1) graph 
    re-extraction for unchanged files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a "medium repo" dummy structure (few files are enough for Big-O assertion)
        for i in range(5):
            file_path = os.path.join(tmpdir, f"module_{i}.py")
            with open(file_path, "w") as f:
                f.write(f"def func_{i}():\n    print('Hello World {i}')\n")

        analyzer = CodeAnalyzer()

        # Run 1: Should parse and visit all 5 files
        with patch("analyst.analyzer.CallGraphVisitor.visit") as mock_visit:
            # We mock visit, so the graph will be empty, but that's fine for testing the cache mechanism
            # Wait, if we mock visit, the cached graph will be empty.
            # But the cache hit logic happens BEFORE the visitor is even instantiated.
            # So as long as we can intercept ast.parse or _parse_cached, it's safer.
            pass

        from analyst.analyzer import _parse_cached as original_parse
        # Actually, let's patch _parse_cached to count how many times files are parsed
        with patch("analyst.analyzer._parse_cached") as mock_parse:
            # Setup a real parse so the rest of the code works
            mock_parse.side_effect = original_parse

            result1 = analyzer.analyze_file(tmpdir)
            
            # Initial run should parse all 5 python files
            assert mock_parse.call_count == 5

            # Run 2: Should hit _GRAPH_CACHE, 0 calls to parse
            mock_parse.reset_mock()
            analyzer2 = CodeAnalyzer()
            result2 = analyzer2.analyze_file(tmpdir)

            # Re-running on unchanged files should NOT invoke parse
            assert mock_parse.call_count == 0

            # Verify the resulting graphs have the same nodes (graphs should be identical)
            assert set(result1["graph"].nodes()) == set(result2["graph"].nodes())
            assert len(result1["graph"].nodes()) == 6  # 5 functions + 1 'print' node
