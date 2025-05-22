"""
CodeScan Library - A library for code analysis and graph database construction.

This package contains modules for analyzing Python code and constructing a graph
database representation of the code structure using Neo4j.
"""

from .constants import (
    NEO4J_HOST,
    NEO4J_PORT_BOLT,
    NEO4J_USER,
    NEO4J_PASSWORD,
    NEO4J_URI,
    TEST_DIR_PATTERNS,
    TEST_FILE_PATTERNS,
    TEST_FUNCTION_PREFIXES,
    TEST_CLASS_PATTERNS,
    IGNORE_DIRS,
    BUILTIN_FUNCTIONS
)

from .utils import (
    is_stdlib_module,
    is_example_file,
    is_test_file,
    is_project_file,
    get_relative_path
)

from .analyzer import CodeAnalyzer
from .db_operations import clear_database, get_db_session, close_db_connection, print_db_info
from .analysis import analyze_file, analyze_directory

__all__ = [
    # Constants
    'NEO4J_HOST', 'NEO4J_PORT_BOLT', 'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_URI',
    'TEST_DIR_PATTERNS', 'TEST_FILE_PATTERNS', 'TEST_FUNCTION_PREFIXES', 'TEST_CLASS_PATTERNS',
    'IGNORE_DIRS', 'BUILTIN_FUNCTIONS',

    # Utility functions
    'is_stdlib_module', 'is_example_file', 'is_test_file', 'is_project_file', 'get_relative_path',

    # Classes
    'CodeAnalyzer',

    # Database operations
    'clear_database', 'get_db_session', 'close_db_connection', 'print_db_info',

    # Analysis functions
    'analyze_file', 'analyze_directory'
]
