import os
import ast
from .constants import IGNORE_DIRS
from .utils import is_test_file, is_example_file, is_project_file, get_relative_path
from .analyzer import CodeAnalyzer

def analyze_file(file_path, session, base_dir, custom_patterns=None):
    """
    Analyze a single Python file and add its content to the graph database.

    Args:
        file_path: Path to the file to analyze
        session: Neo4j database session
        base_dir: Base directory of the project for relative path computation
        custom_patterns: Dictionary with custom test detection patterns
    """
    # Skip standard library files
    if not is_project_file(file_path, base_dir):
        print(f"Skipping non-project file: {file_path}")
        return

    # Convert to relative path for storage
    rel_path = get_relative_path(file_path, base_dir)

    # Check if file is a test file or example file
    is_test = is_test_file(rel_path, custom_patterns)
    is_example = is_example_file(rel_path)

    file_type = "test" if is_test else "example" if is_example else "production"

    with open(file_path, "r", encoding="utf-8") as f:
        print(f"Analyzing file: {rel_path} (from {file_path}) - {file_type} file")
        try:
            tree = ast.parse(f.read(), filename=file_path)
            # Pass the test file flag to CodeAnalyzer
            analyzer = CodeAnalyzer(rel_path, session, is_test_file=is_test)
            analyzer.visit(tree)

            # Process test relationships if this is a test file
            if is_test:
                analyzer.process_test_relationships(custom_patterns)

        except SyntaxError as e:
            print(f"Syntax error in {rel_path}: {e}")
        except UnicodeDecodeError:
            print(f"Unable to decode file: {rel_path} - skipping")

def analyze_directory(directory, session, ignore_dirs=None, custom_patterns=None):
    """
    Recursively analyze all Python files in a directory and its subdirectories.

    Args:
        directory: Directory to scan
        session: Neo4j database session
        ignore_dirs: List of directory names to ignore (defaults to IGNORE_DIRS)
        custom_patterns: Dictionary with custom test detection patterns
    """
    if ignore_dirs is None:
        ignore_dirs = IGNORE_DIRS

    # Store the base directory to identify project files
    base_dir = os.path.abspath(directory)

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                analyze_file(full_path, session, base_dir, custom_patterns)
