# Test Labeling Requirements

This document outlines the requirements for labeling test components in the CodeScan tool.

## Overview

The current CodeScan implementation uses Neo4j to create a graph database of code components and their relationships. To improve test visibility and analysis, we need to enhance the scanner to properly label test components.

## Requirements

1. **Test Label for All Test Components**
   - All classes and functions in the tests folder must have the `Test` label
   - This provides a base identifier for any test component

2. **TestClass Label for Test Classes**
   - All classes residing in tests folder must have an additional `TestClass` label
   - This helps distinguish test classes from test functions

3. **TestFunction Label for Test Functions**
   - All functions residing in tests folder must have the `TestFunction` label
   - This helps in filtering and analyzing test functions separately

## Cross-Repository Support

Since the CodeScan tool will be used across different Python repositories with varying structures, we need flexibility in test detection:

1. **Configurable Test Directories**
   - Support multiple test directory patterns (e.g., `tests/`, `test/`, `testing/`)
   - Allow custom configuration via environment variables or command-line arguments

2. **Configurable Test File Patterns**
   - Support common test file patterns (e.g., `test_*.py`, `*_test.py`)
   - Allow custom configuration based on project conventions

3. **Configurable Test Function Patterns**
   - Support common test function naming (e.g., `test_*`)
   - Allow custom prefixes/suffixes based on project conventions

4. **Configurable Test Class Patterns**
   - Support common test class naming (e.g., `Test*`, `*Test`)
   - Allow custom patterns based on project conventions

## Implementation Approach

To implement these requirements, we need to modify the `CodeAnalyzer` class in `scanner.py` to:

1. Add configuration options for test detection patterns
2. Detect when a file is being analyzed from within a test directory or matches test file patterns
3. Add the appropriate labels when creating nodes for classes and functions
4. Update the existing Node creation Cypher queries to include these additional labels

## File Changes Needed

The primary file to modify is `scanner.py`, specifically:

- Add configuration variables for test patterns
- Add a flexible `is_test_file` detection function
- The `analyze_file` function to detect test files using the flexible detection
- The `visit_ClassDef` method to add test-related labels to classes
- The `visit_FunctionDef` method to add test-related labels to functions

## Examples

### Configuration Example
```python
# Default patterns - can be overridden
TEST_DIR_PATTERNS = os.getenv("TEST_DIR_PATTERNS", "tests/,test/,testing/").split(",")
TEST_FILE_PATTERNS = os.getenv("TEST_FILE_PATTERNS", "test_*.py,*_test.py").split(",")
TEST_FUNCTION_PREFIXES = os.getenv("TEST_FUNCTION_PREFIXES", "test_").split(",")
TEST_CLASS_PATTERNS = os.getenv("TEST_CLASS_PATTERNS", "Test*,*Test").split(",")
```

### Test File Detection Example
```python
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
```

### Class Example
```python
# In scanner.py, visit_ClassDef method
if is_test_file:
    self.session.run(
        "MERGE (c:Class:Test:TestClass {name: $name, file: $file, line: $line, end_line: $end_line})",
        name=class_name,
        file=self.file_path,
        line=line_num,
        end_line=getattr(node, 'end_lineno', -1)
    )
else:
    # Regular class creation (existing code)
```

### Function Example
```python
# In scanner.py, visit_FunctionDef method
if is_test_file:
    labels = ":Function:Test:TestFunction"
    # Rest of the function...
else:
    labels = ":Function"
    # Existing logic...
```
