# Implementation Plan for Test Components in CodeScan

This document outlines the plan for implementing test component labeling and test coverage detection in the CodeScan tool.

## Phase 1: Test Component Labeling with Cross-Repository Support

### Goal
Add proper labels to all test-related components in the code graph with flexibility to work across different Python repositories.

### Tasks

1. **Add Configuration for Test Pattern Detection**
   - Define configurable patterns for test directories, files, functions, and classes
   - Support configuration via environment variables and command-line arguments
   - Create a flexible test detection mechanism

2. **Modify Scanner.py to Detect Test Files**
   - Implement a flexible `is_test_file` function for cross-repository compatibility
   - Add a flag in the `CodeAnalyzer` class to track test files

3. **Update Class Node Creation**
   - Modify the `visit_ClassDef` method to add `Test` and `TestClass` labels for classes in test files
   - Preserve existing functionality for non-test classes

4. **Update Function Node Creation**
   - Modify the `visit_FunctionDef` method to add `Test` and `TestFunction` labels for functions in test files
   - Preserve existing functionality for non-test functions

5. **Implement Test Queries in MCP Server**
   - Add new tools in `codescan_mcp_server.py` to query test classes and functions
   - Examples: `list_test_classes()`, `list_test_functions()`

### Implementation Details

```python
# Configuration for test patterns
TEST_DIR_PATTERNS = os.getenv("TEST_DIR_PATTERNS", "tests/,test/,testing/").split(",")
TEST_FILE_PATTERNS = os.getenv("TEST_FILE_PATTERNS", "test_*.py,*_test.py").split(",")
TEST_FUNCTION_PREFIXES = os.getenv("TEST_FUNCTION_PREFIXES", "test_").split(",")
TEST_CLASS_PATTERNS = os.getenv("TEST_CLASS_PATTERNS", "Test*,*Test").split(",")

# Flexible test file detection
def is_test_file(file_path):
    """Determine if a file is a test file based on configured patterns."""
    # Check if file is in a test directory
    for pattern in TEST_DIR_PATTERNS:
        if pattern in file_path or file_path.startswith(pattern):
            return True

    # Check if filename matches test file patterns
    filename = os.path.basename(file_path)
    for pattern in TEST_FILE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True

    return False

# Detecting test files (in analyze_file function)
is_test = is_test_file(rel_path)
analyzer = CodeAnalyzer(rel_path, session, is_test_file=is_test)

# Updated CodeAnalyzer initialization
def __init__(self, file_path, session, is_test_file=False):
    self.file_path = file_path
    self.session = session
    self.current_class = None
    self.current_function = None
    self.is_test_file = is_test_file
```

## Phase 2: Test Coverage Detection

### Goal
Establish relationships between test components and the production code they test.

### Tasks

1. **Create the TESTS Relationship**
   - Define a new relationship type in the Neo4j graph
   - Set up visualization properties (color, etc.)

2. **Implement Configurable Naming Pattern Detection**
   - For each test function and class, analyze its name using configurable patterns
   - Look for matching production code components
   - Create TESTS relationships when found

3. **Implement Import Tracking**
   - Add `visit_Import` and `visit_ImportFrom` methods to CodeAnalyzer
   - Track imports in test files
   - Establish relationships between test code and imported production code

4. **Enhance Call Analysis**
   - Update the call tracking to identify when test code calls production code
   - Create TESTS relationships based on call patterns

5. **Add Test Coverage Queries**
   - Add MCP tools to query test coverage
   - Examples: `untested_functions()`, `test_coverage_ratio()`

### Implementation Details

```python
# Configurable naming pattern detection
def process_test_relationships(self):
    if not self.is_test_file:
        return

    # Process based on configurable naming patterns
    for prefix in TEST_FUNCTION_PREFIXES:
        prefix_len = len(prefix)
        self.session.run("""
            MATCH (test:TestFunction)
            WHERE test.name STARTS WITH $prefix
            WITH test, substring(test.name, $prefix_len) AS tested_name
            MATCH (prod:Function)
            WHERE NOT prod:TestFunction AND prod.name = tested_name
            MERGE (test)-[:TESTS {method: 'naming_pattern'}]->(prod)
        """, prefix=prefix, prefix_len=prefix_len)
```

## Phase 3: Testing and Documentation

### Goals
- Ensure all new functionality works correctly across different repository structures
- Document the new features for users

### Tasks

1. **Write Tests**
   - Add tests for test component labeling with different repository structures
   - Add tests for test coverage detection with different naming conventions
   - Update existing tests as needed

2. **Update Documentation**
   - Update README.md with new features
   - Document configurable test patterns
   - Document the new Cypher queries for test analysis
   - Create examples for test coverage queries

3. **Create Visualization Guide**
   - Document how to visualize test coverage in Neo4j Browser
   - Create example queries for test visualization

## Files to Update

1. **scanner.py**
   - Add test pattern configuration
   - Add flexible test file detection
   - Modify node creation for test components
   - Add test relationship creation

2. **codescan_mcp_server.py**
   - Add configuration management tools
   - Add new tools for test queries
   - Add test coverage analysis tools

## Command-Line Support

Add command-line argument support for configuring test patterns:

```python
def main():
    import argparse

    parser = argparse.ArgumentParser(description='Scan Python code and build a Neo4j graph')

    # Configuration options
    parser.add_argument('--test-dirs', dest='test_dirs',
                        default=','.join(TEST_DIR_PATTERNS),
                        help='Comma-separated list of test directory patterns')
    parser.add_argument('--test-files', dest='test_files',
                        default=','.join(TEST_FILE_PATTERNS),
                        help='Comma-separated list of test file patterns')
    # ... other arguments ...
```

## Delivery Timeline

1. Phase 1: Test Component Labeling - 2-3 days
2. Phase 2: Test Coverage Detection - 2-3 days
3. Phase 3: Testing and Documentation - 1-2 days

Total estimated time: 5-8 days
