import ast
import os
import networkx as nx
from typing import Dict, Any, List, Optional

class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.graph = nx.DiGraph()
        self.current_scope = "global"
        self.definitions = []
        self.file_path = file_path

    def visit_FunctionDef(self, node):
        previous_scope = self.current_scope
        function_name = node.name
        # If in a class, prefix with class name (simplified)
        if self.current_scope != "global" and not self.current_scope.endswith("<module>"):
             full_name = f"{self.current_scope}.{function_name}"
        else:
             full_name = function_name

        self.current_scope = full_name

        # Entry-point heuristics:
        #   1. Well-known names: main, run, app
        #   2. Any function at module (global) level
        is_entry = (
            function_name in ["main", "run", "app"]
            or previous_scope in ("global", "<module>")
        )
        self.graph.add_node(
            full_name,
            type="function",
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
            file=self.file_path,
            entry_point=is_entry,
        )
        self.definitions.append({"name": full_name, "type": "function", "lineno": node.lineno})
        
        self.generic_visit(node)
        self.current_scope = previous_scope

    def visit_ClassDef(self, node):
        previous_scope = self.current_scope
        class_name = node.name
        self.current_scope = class_name
        
        self.graph.add_node(
            class_name,
            type="class",
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
            file=self.file_path,
            entry_point=False,
        )
        self.definitions.append({"name": class_name, "type": "class", "lineno": node.lineno})

        self.generic_visit(node)
        self.current_scope = previous_scope

    def visit_Call(self, node):
        callee_name = self._get_callee_name(node)
        if callee_name:
            self.graph.add_edge(self.current_scope, callee_name)
        self.generic_visit(node)

    def _get_callee_name(self, node) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr # Simplified: extracts method name only
        return None

class CodeAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.definitions = []
        self.errors = []

    def analyze_file(self, target_path: str) -> Dict[str, Any]:
        """
        Analyzes a file or directory recursively.
        """
        # Reset graph and errors for fresh analysis
        self.graph = nx.DiGraph()
        self.definitions = []
        self.errors = []

        if not os.path.exists(target_path):
            return {"error": f"Path not found: {target_path}"}
            
        if os.path.isdir(target_path):
            return self._analyze_directory(target_path)
        else:
            return self._analyze_single_file(target_path)

    def _analyze_directory(self, dir_path: str) -> Dict[str, Any]:
        # Clear state for a fresh directory analysis
        self.graph = nx.DiGraph() 
        self.definitions = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    # Skip venv/node_modules/etc
                    if "site-packages" in full_path or "node_modules" in full_path or "__pycache__" in full_path:
                        continue
                        
                    self._analyze_single_file(full_path, merge=True)
                    
        return {
            "file": dir_path,
            "definitions": self.definitions,
            "graph": self.graph,
            "errors": self.errors
        }

    def _analyze_single_file(self, file_path: str, merge: bool = False) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
            except SyntaxError as e:
                 # In directory mode, we might just log this and continue
                if merge:
                    error_msg = f"Syntax error in {file_path}: {e}"
                    print(error_msg)
                    self.errors.append(error_msg)
                    return {}
                return {"error": f"Syntax error in {file_path}: {e}"}

        visitor = CallGraphVisitor(file_path)
        visitor.visit(tree)
        
        if merge:
            self.graph = nx.compose(self.graph, visitor.graph)
            self.definitions.extend(visitor.definitions)
        else:
            self.graph = visitor.graph
            self.definitions = visitor.definitions
        
        return {
            "file": file_path,
            "definitions": visitor.definitions,
            "graph": visitor.graph
        }

    def analyze_structure(self, file_path: str) -> str:
        result = self.analyze_file(file_path)
        if "error" in result:
            return result["error"]

        graph = result["graph"]
        summary = f"Target: {result['file']}\n"
        summary += f"Nodes ({graph.number_of_nodes()}): {', '.join(graph.nodes())}\n"
        summary += f"Edges ({graph.number_of_edges()}): {list(graph.edges())}\n"
        return summary

    # ------------------------------------------------------------------
    # Dependency extraction via import analysis
    # ------------------------------------------------------------------

    def extract_dependencies(
        self, file_path: str, project_root: str | None = None
    ) -> Dict[str, Any]:
        """
        Extracts import statements from *file_path* using AST.

        Parameters
        ----------
        file_path : str
            Path to the Python source file.
        project_root : str, optional
            Root of the project. Used to detect local (project-internal)
            imports by checking whether a corresponding ``.py`` file exists.
            Defaults to the directory containing *file_path*.

        Returns
        -------
        dict with keys ``file`` and ``dependencies``.
        Each dependency: ``{"module": str, "names": [str], "is_local": bool}``
        """
        resolved = os.path.abspath(file_path)
        if not os.path.isfile(resolved):
            return {"error": f"File not found: {file_path}"}

        if project_root is None:
            project_root = os.path.dirname(resolved)
        project_root = os.path.abspath(project_root)

        try:
            with open(resolved, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=resolved)
        except SyntaxError as e:
            return {"error": f"Syntax error in {file_path}: {e}"}

        dependencies: List[Dict[str, Any]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    dependencies.append({
                        "module": module,
                        "names": [alias.asname or alias.name],
                        "is_local": self._is_local_module(module, project_root),
                    })

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                # Relative imports (level > 0) are always local
                is_local = (
                    node.level > 0
                    or self._is_local_module(module, project_root)
                )
                dependencies.append({
                    "module": module,
                    "names": names,
                    "is_local": is_local,
                })

        return {"file": file_path, "dependencies": dependencies}

    @staticmethod
    def _is_local_module(module_name: str, project_root: str) -> bool:
        """Check whether *module_name* maps to a .py file under *project_root*."""
        parts = module_name.split(".")
        # Try as a package (directory with __init__.py) or plain .py file
        candidate_file = os.path.join(project_root, *parts) + ".py"
        candidate_pkg = os.path.join(project_root, *parts, "__init__.py")
        return os.path.isfile(candidate_file) or os.path.isfile(candidate_pkg)
