import os
import sys
import tempfile
import shutil
import unittest
import ast
from unittest.mock import MagicMock, patch

# Add parent directory to path to import scanner module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module we'll be testing
from scanner import CodeAnalyzer

class TestCoverageDetection(unittest.TestCase):
    """Test the test coverage detection functionality."""

    def setUp(self):
        """Set up the test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_mock = MagicMock()

        # Create a sample test file with imports and calls
        self.test_file_path = os.path.join(self.temp_dir, "test_file.py")
        with open(self.test_file_path, "w") as f:
            f.write("""
import scanner  # Direct import
from scanner import CodeAnalyzer  # Import from

class TestCodeAnalyzer:
    def test_visit_call(self):
        analyzer = CodeAnalyzer("test.py", None)
        analyzer.visit_call(None)

def test_analyze_file():
    scanner.analyze_file("test.py", None, ".")
""")

        # Create a production file that will be "tested"
        self.prod_file_path = os.path.join(self.temp_dir, "scanner.py")
        with open(self.prod_file_path, "w") as f:
            f.write("""
class CodeAnalyzer:
    def visit_call(self, node):
        pass

def analyze_file(file_path, session, base_dir):
    pass
""")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_visit_import_tracking(self):
        """Test that imports in test files are tracked correctly."""
        # Parse the test file
        with open(self.test_file_path, "r") as f:
            tree = ast.parse(f.read(), filename=self.test_file_path)

        # Create an analyzer with is_test_file=True
        analyzer = CodeAnalyzer(self.test_file_path, self.session_mock, is_test_file=True)

        # Find the Import node
        import_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(alias.name == "scanner" for alias in node.names):
                import_node = node
                break

        # Call visit_Import with the node
        analyzer.visit_Import(import_node)

        # Verify the correct Cypher query was called to track the import
        found_import_tracking = False
        for call in self.session_mock.run.call_args_list:
            if "MERGE (i:Import" in call[0][0] and "scanner" in str(call):
                found_import_tracking = True
                break

        self.assertTrue(found_import_tracking, "Import tracking not found in session calls")

    def test_visit_importfrom_tracking(self):
        """Test that import from statements in test files are tracked correctly."""
        # Parse the test file
        with open(self.test_file_path, "r") as f:
            tree = ast.parse(f.read(), filename=self.test_file_path)

        # Create an analyzer with is_test_file=True
        analyzer = CodeAnalyzer(self.test_file_path, self.session_mock, is_test_file=True)

        # Find the ImportFrom node
        importfrom_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "scanner":
                importfrom_node = node
                break

        # Call visit_ImportFrom with the node
        analyzer.visit_ImportFrom(importfrom_node)

        # Verify the correct Cypher query was called to track the import
        found_import_tracking = False
        for call in self.session_mock.run.call_args_list:
            if "MERGE (i:Import" in call[0][0] and "CodeAnalyzer" in str(call):
                found_import_tracking = True
                break

        self.assertTrue(found_import_tracking, "ImportFrom tracking not found in session calls")

    def test_process_test_relationships_naming(self):
        """Test that test relationships are created based on naming patterns."""
        # Create an analyzer with is_test_file=True
        analyzer = CodeAnalyzer(self.test_file_path, self.session_mock, is_test_file=True)

        # Call the method to create test relationships
        analyzer.process_test_relationships()

        # Verify the correct Cypher query was called to create naming-based relationships
        found_naming_relationship = False
        for call in self.session_mock.run.call_args_list:
            if "MATCH (test:TestFunction)" in call[0][0] and "STARTS WITH" in call[0][0] and "MERGE (test)-[:TESTS" in call[0][0]:
                found_naming_relationship = True
                break

        self.assertTrue(found_naming_relationship, "Naming-based test relationship creation not found")

    def test_process_test_relationships_imports(self):
        """Test that test relationships are created based on imports."""
        # Create an analyzer with is_test_file=True
        analyzer = CodeAnalyzer(self.test_file_path, self.session_mock, is_test_file=True)

        # Call the method to create test relationships
        analyzer.process_test_relationships()

        # Verify the correct Cypher query was called to create import-based relationships
        found_import_relationship = False
        for call in self.session_mock.run.call_args_list:
            if "MATCH (test:TestFunction)-[:IMPORTS]->(i:Import)" in call[0][0] and "MERGE (test)-[:TESTS" in call[0][0]:
                found_import_relationship = True
                break

        self.assertTrue(found_import_relationship, "Import-based test relationship creation not found")

    def test_process_test_relationships_calls(self):
        """Test that test relationships are created based on calls."""
        # Create an analyzer with is_test_file=True
        analyzer = CodeAnalyzer(self.test_file_path, self.session_mock, is_test_file=True)

        # Call the method to create test relationships
        analyzer.process_test_relationships()

        # Verify the correct Cypher query was called to create call-based relationships
        found_call_relationship = False
        for call in self.session_mock.run.call_args_list:
            if "MATCH (test:TestFunction)-[:CALLS]->(prod:Function)" in call[0][0] and "MERGE (test)-[:TESTS" in call[0][0]:
                found_call_relationship = True
                break

        self.assertTrue(found_call_relationship, "Call-based test relationship creation not found")

    def test_analyze_file_calls_process_test_relationships(self):
        """Test that analyze_file calls process_test_relationships for test files."""
        # Mock the CodeAnalyzer class
        with patch('scanner.CodeAnalyzer') as mock_analyzer_class:
            # Setup the mock instance that will be created
            mock_analyzer_instance = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer_instance

            # Create a real session mock
            session_mock = MagicMock()

            # Import the analyze_file function
            from scanner import analyze_file

            # Call analyze_file with is_test=True
            analyze_file(self.test_file_path, session_mock, self.temp_dir)

            # Verify process_test_relationships was called on the analyzer instance
            mock_analyzer_instance.process_test_relationships.assert_called_once()

if __name__ == "__main__":
    unittest.main()
