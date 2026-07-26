# Adding a New Language to VibeGraph

VibeGraph's language analysis subsystem is designed to be highly extensible. This guide explains how to add support for a new programming language by implementing a language plugin using our `LanguageAnalyzer` architecture.

In this comprehensive guide, we'll walk through the entire process using a hypothetical **Ruby** implementation as our working example. We will cover the contract you must fulfill, how to structure the plugin, how to hook it into the main application, and what testing is required.

## 1. The `LanguageAnalyzer` Protocol Contract

All language plugins in VibeGraph must implement the `LanguageAnalyzer` protocol, which is explicitly defined in `analyst/languages/base.py`. This contract ensures a consistent interface for the core engine, allowing VibeGraph to handle any supported language seamlessly without needing language-specific logic in the main resolution loops.

The protocol requires implementing the following key methods and properties:

- `analyze_file(file_path: Path) -> FileAnalysis`: This is the core analysis engine of your plugin. It is responsible for parsing the source code file, extracting defined functions and classes, cross-referencing module imports, and recording all function or method calls made within the file.
- `module_id_from_path(file_path: Path) -> str`: Converts a physical filesystem path into a canonical, logical module identifier that the language ecosystem uses (e.g., converting `src/utils/math.py` to `src.utils.math`). This identifier is critical for resolving cross-file references.
- `get_local_modules() -> Set[str]`: Returns a set of all local modules discovered in the analyzed workspace for this specific language. This helps the engine distinguish between local workspace imports and external package imports.
- `builtins`: A property returning a predefined set of language built-in identifiers (e.g., `puts`, `Array`, `Hash` in Ruby). VibeGraph uses this to filter out noise when attempting to resolve dependency nodes.
- `stdlib_modules`: A property returning a predefined set of standard library modules available natively in the language (e.g., `json`, `net/http` in Ruby). This helps categorize edges in the final graph.

## 2. The `FileAnalysis` Dataclass and Record Shapes

The expected output of the `analyze_file` method must always be an instance of the `FileAnalysis` dataclass (also defined in `base.py`). This standardized structure powers VibeGraph's overarching dependency graph construction.

The dataclass contains four critical fields:
- `module_id`: The canonical module identifier generated for the file.
- `definitions`: A list of strings representing the nodes (functions, classes, modules) defined in this file.
- `imports`: A dictionary tracking external and internal dependencies.
- `pending_calls`: A list of unresolved function/method calls discovered in the file that will be linked later in the analysis pipeline.

### Shapes of `imports` and `pending_calls`

**`imports`**
The `imports` record must be a mapping of `str` to `str` where the key represents the local name or alias used within the file, and the value represents the canonical source module.
```python
# Example for a Ruby file containing:
# require 'json'
# require 'net/http'
imports = {"json": "json", "net/http": "net/http"}
```

**`pending_calls`**
The `pending_calls` record is a list of dictionaries. Each dictionary represents a function or method call that needs to be resolved against the codebase graph. Each call typically records:
```python
pending_calls = [
    {
        # The fully qualified context where the call occurred
        "caller": "MyApplication::User.save",
        # The function/method being invoked
        "callee": "puts",
        # The line number where the call is made (used for diagnostics)
        "line": 42,
    }
]
```

## 3. Tree-Sitter Loading via `analyst/tree_sitter_loader.py`

VibeGraph relies heavily on [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) for fast, robust, and error-tolerant parsing. The `analyst/tree_sitter_loader.py` module manages the downloading, compilation, and loading of language grammars.

When adding a new language, you do not need to manually compile tree-sitter libraries. You typically need to:
1. Ensure the relevant tree-sitter language package (e.g., `tree-sitter-ruby`) is added to the project dependencies.
2. Rely on the `tree_sitter_loader` to dynamically compile and load the `.so`/`.dylib` grammar if it's not already cached on the system.
3. In your plugin's initialization phase, request the language from the loader.

```python
from analyst.tree_sitter_loader import get_language

# Returns the compiled tree-sitter Language object for 'ruby'
ruby_lang = get_language("ruby")

# This can then be passed to a tree_sitter.Parser instance
# parser = tree_sitter.Parser()
# parser.set_language(ruby_lang)
```

## 4. Registering the Plugin in `__init__.py`

For VibeGraph to utilize your new analyzer, the plugin must be registered in the central dispatcher located at `analyst/languages/__init__.py`. This registry maps file extensions to the appropriate analyzer class.

To register your plugin, simply import your class and update the `ANALYZERS` dictionary:

```python
# analyst/languages/__init__.py

from .python import PythonAnalyzer
from .javascript import JavaScriptAnalyzer
from .ruby import RubyAnalyzer  # 1. Import your new analyzer class

# The central registry mapping file extensions to analyzers
ANALYZERS = {
    ".py": PythonAnalyzer,
    ".js": JavaScriptAnalyzer,
    ".ts": JavaScriptAnalyzer,
    ".rb": RubyAnalyzer,  # 2. Map the .rb extension to your RubyAnalyzer
}
```

## 5. Walkthrough: A Hypothetical Ruby Plugin

Let's look at what the file structure and full implementation for a Ruby plugin would actually look like in practice.

### File Structure Overview
When adding Ruby support, you would create the following structure:
```
analyst/
  languages/
    __init__.py       # (Modified) Updated with RubyAnalyzer registry
    base.py           # (Unmodified) Contains the Protocol and Dataclasses
    ruby.py           # (NEW) The Ruby plugin implementation
tests/
  languages/
    test_ruby.py      # (NEW) The parity tests for the Ruby plugin
```

### The `RubyAnalyzer` Implementation (`analyst/languages/ruby.py`)

Here is a functional, simplified version of what `ruby.py` would look like, implementing the required methods:

```python
from pathlib import Path
from typing import Set, Dict, List
import tree_sitter

from analyst.languages.base import LanguageAnalyzer, FileAnalysis
from analyst.tree_sitter_loader import get_language


class RubyAnalyzer(LanguageAnalyzer):
    """
    Analyzer implementation for the Ruby programming language.
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

        # 1. Load the Tree-sitter grammar
        self.language = get_language("ruby")
        self.parser = tree_sitter.Parser()
        self.parser.set_language(self.language)

        # In a real plugin, this would be populated by an initial workspace scan
        self._local_modules: Set[str] = set()

    @property
    def builtins(self) -> Set[str]:
        """Return Ruby built-in methods and classes."""
        return {
            "puts",
            "print",
            "require",
            "require_relative",
            "Array",
            "String",
            "Hash",
            "Object",
        }

    @property
    def stdlib_modules(self) -> Set[str]:
        """Return standard Ruby library modules."""
        return {"json", "net/http", "yaml", "fileutils", "date", "time"}

    def get_local_modules(self) -> Set[str]:
        """Return discovered local modules in the workspace."""
        return self._local_modules

    def module_id_from_path(self, file_path: Path) -> str:
        """
        Convert file paths to Ruby require paths.
        e.g., 'lib/myapp/models/user.rb' -> 'lib/myapp/models/user'
        """
        try:
            rel_path = file_path.relative_to(self.workspace_root)
            return str(rel_path.with_suffix(""))
        except ValueError:
            return file_path.stem

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """
        Parse the Ruby file and extract definitions, imports, and calls.
        """
        module_id = self.module_id_from_path(file_path)

        try:
            source_code = file_path.read_text(encoding="utf-8")
        except Exception:
            # Failsafe for unreadable files
            return FileAnalysis(
                module_id=module_id, definitions=[], imports={}, pending_calls=[]
            )

        # Parse the source code using Tree-sitter
        tree = self.parser.parse(source_code.encode("utf-8"))
        root_node = tree.root_node

        definitions: List[str] = []
        imports: Dict[str, str] = {}
        pending_calls: List[Dict] = []

        # A basic recursive AST traversal function
        def traverse(node):
            # Record Requires (Imports)
            if node.type == "method_call" and node.child_by_field_name("method"):
                method_name_bytes = source_code[
                    node.child_by_field_name(
                        "method"
                    ).start_byte : node.child_by_field_name("method").end_byte
                ]

                if method_name_bytes in (b"require", b"require_relative"):
                    args = node.child_by_field_name("arguments")
                    if args and args.child_count > 0:
                        # Extract the string argument being required
                        req_str = (
                            source_code[
                                args.children[0].start_byte : args.children[0].end_byte
                            ]
                            .decode("utf-8")
                            .strip("'\"")
                        )
                        imports[req_str] = req_str

            # Record Definitions (Classes or Modules)
            if node.type in ("class", "module"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source_code[
                        name_node.start_byte : name_node.end_byte
                    ].decode("utf-8")
                    definitions.append(f"{module_id}::{name}")

            # Record Method Calls
            if node.type == "call":
                method_node = node.child_by_field_name("method")
                if method_node:
                    callee = source_code[
                        method_node.start_byte : method_node.end_byte
                    ].decode("utf-8")
                    pending_calls.append(
                        {
                            "caller": module_id,  # Simplified caller context for demonstration
                            "callee": callee,
                            "line": node.start_point[0] + 1,
                        }
                    )

            # Recurse through children
            for child in node.children:
                traverse(child)

        # Execute traversal
        traverse(root_node)

        return FileAnalysis(
            module_id=module_id,
            definitions=definitions,
            imports=imports,
            pending_calls=pending_calls,
        )
```

## 6. Testing Requirements

A new language plugin is strictly required to have exhaustive parity tests before it can be merged. These tests ensure your language parses constructs exactly how the VibeGraph engine expects and prevents future regressions.

Tests must be placed in `tests/languages/`. A typical test file (`test_ruby.py`) uses `pytest` and verifies that `analyze_file` correctly extracts imports, definitions, and calls using a temporary workspace.

### Example Unit Test (`tests/languages/test_ruby.py`)

Here is an example test verifying the core functionality of our `RubyAnalyzer`:

```python
import pytest
from pathlib import Path
from analyst.languages.ruby import RubyAnalyzer


def test_ruby_analyzer_basic_extraction(tmp_path: Path):
    """Test that the RubyAnalyzer correctly extracts imports, definitions, and calls."""
    # Setup a temporary test workspace
    workspace = tmp_path / "ruby_app"
    workspace.mkdir()

    # Create a sample ruby file with various constructs
    main_rb = workspace / "main.rb"
    main_rb.write_text("""
require 'json'
require_relative 'models/user'

class Application
  def run
    puts "Starting application process..."
    user = User.new
    user.save
  end
end
""")

    # Initialize the Ruby analyzer
    analyzer = RubyAnalyzer(workspace_root=workspace)

    # Analyze the file
    analysis = analyzer.analyze_file(main_rb)

    # Assert Module ID generation
    assert analysis.module_id == "main"

    # Assert Imports were detected
    assert "json" in analysis.imports
    assert "models/user" in analysis.imports

    # Assert Class Definitions were recorded
    assert any("Application" in defn for defn in analysis.definitions)

    # Assert Function/Method Calls were extracted
    calls = [call["callee"] for call in analysis.pending_calls]
    assert "puts" in calls
    assert "new" in calls
    assert "save" in calls
```

### Required Test Coverage Checklist

When submitting your Pull Request, ensure your tests thoroughly cover:
1. **Basic parsing:** Classes, functions, nested modules.
2. **Imports:** Standard library requires, third-party gems, relative local requires.
3. **Calls:** Standalone function calls, method chaining, static/class method calls.
4. **Edge Cases:** Handling of syntax errors gracefully, empty files, deeply nested directory structures.
5. **Cross-Language Interaction (Optional):** If the language heavily interacts with others (e.g., C extensions for Python), testing edge cases is highly encouraged.

By following these guidelines and fulfilling the protocol contract, your language plugin will integrate smoothly and robustly into VibeGraph's analysis engine.
