import unittest
import networkx as nx
import sys
import os

# Add project root to sys.path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from teacher.basic_reporter import BasicTeacher

class TestBasicTeacher(unittest.TestCase):
    def setUp(self):
        self.teacher = BasicTeacher()

    def test_generate_lesson_empty_graph(self):
        empty_graph = nx.DiGraph()
        file_path = "empty_module.py"

        lesson = self.teacher.generate_lesson(empty_graph, file_path)

        # Verify basic structure
        self.assertIn(f"# Lesson: Understanding {file_path}", lesson)
        self.assertIn("## 1. Structural Overview", lesson)
        self.assertIn("## 2. Key Interactions", lesson)
        self.assertIn("No internal function calls detected in this file.", lesson)
        self.assertIn("## 3. Analysis", lesson)
        self.assertIn("This module is **loosely coupled** (few connections).", lesson)

if __name__ == '__main__':
    unittest.main()
