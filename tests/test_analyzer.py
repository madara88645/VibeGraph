import os
import tempfile
import unittest
from analyst.analyzer import CodeAnalyzer

class TestCodeAnalyzerStructure(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dummy_file = os.path.join(self.tmpdir, "dummy.py")
        self.dummy_code = '''def helper():\n    pass\n\ndef main():\n    helper()\n'''
        with open(self.dummy_file, "w", encoding="utf-8") as f:
            f.write(self.dummy_code)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
