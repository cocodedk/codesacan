import os
import ast
from typing import Optional, Dict, Any, List
from tqdm import tqdm

from .constants import IGNORE_DIRS
from .utils import is_test_file, is_example_file, is_project_file, get_relative_path
from .analyzer import CodeAnalyzer
from .stats_collector import StatsCollector

def analyze_file(file_path: str, session, base_dir: str, stats_collector: Optional[StatsCollector] = None,
                custom_patterns: Optional[Dict[str, Any]] = None) -> None:
    """
    Analyze a single Python file and add its content to the graph database.

    Args:
        file_path: Path to the file to analyze
        session: Neo4j database session
        base_dir: Base directory of the project for relative path computation
        stats_collector: Statistics collector to use
        custom_patterns: Dictionary with custom test detection patterns
    """
    # Use provided stats collector or create a new one
    stats = stats_collector if stats_collector is not None else StatsCollector()

    # Skip standard library files
    if not is_project_file(file_path, base_dir):
        stats.register_skipped_file(file_path, "Not a project file")
        return

    # Convert to relative path for storage
    rel_path = get_relative_path(file_path, base_dir)

    # Check if file is a test file or example file
    is_test_flag = is_test_file(rel_path, custom_patterns)
    is_example_flag = is_example_file(rel_path)

    file_type = "test" if is_test_flag else "example" if is_example_flag else "production"

    # Register file with stats collector
    stats.register_file(rel_path, file_type)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
            # Pass the test file flag and stats collector to CodeAnalyzer
            analyzer = CodeAnalyzer(rel_path, session, is_test_file=is_test_flag, stats_collector=stats)
            analyzer.visit(tree)

            # Process test relationships if this is a test file
            if is_test_flag:
                analyzer.process_test_relationships(custom_patterns)

    except SyntaxError as e:
        stats.register_file_error(rel_path, "SyntaxError", str(e))
    except UnicodeDecodeError:
        stats.register_file_error(rel_path, "UnicodeDecodeError", "Unable to decode file")

def analyze_directory(directory: str, session, ignore_dirs: Optional[List[str]] = None,
                    custom_patterns: Optional[Dict[str, Any]] = None, verbose: bool = False) -> StatsCollector:
    """
    Recursively analyze all Python files in a directory and its subdirectories.

    Args:
        directory: Directory to scan
        session: Neo4j database session
        ignore_dirs: List of directory names to ignore (defaults to IGNORE_DIRS)
        custom_patterns: Dictionary with custom test detection patterns
        verbose: Whether to print verbose output during scanning

    Returns:
        Statistics collector with information about the analysis
    """
    if ignore_dirs is None:
        ignore_dirs = IGNORE_DIRS

    # Create a stats collector
    stats = StatsCollector(verbose=verbose)

    # Store the base directory to identify project files
    base_dir = os.path.abspath(directory)

    # First count how many Python files we need to process for the progress bar
    total_files = 0
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to avoid traversing ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        total_files += sum(1 for file in files if file.endswith(".py"))

    # Now process the files with a progress bar
    with tqdm(total=total_files, desc="Analyzing files", unit="file") as pbar:
        for root, dirs, files in os.walk(directory):
            # Modify dirs in-place to avoid traversing ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    analyze_file(full_path, session, base_dir, stats, custom_patterns)
                    pbar.update(1)

    # Return the stats collector for the caller to use
    return stats
