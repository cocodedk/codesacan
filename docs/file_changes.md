# Required File Changes for Test Labeling and Coverage Detection

This document outlines the specific changes needed in each file to implement test component labeling and test coverage detection.

## Configuration for Repository Flexibility

To ensure the scanner works across different Python repositories with varying test structures, we need to add configuration options:

```python
# Add to scanner.py or in a separate config.py file
import os
import fnmatch

# Default patterns - can be overridden via environment variables or command-line args
TEST_DIR_PATTERNS = os.getenv("TEST_DIR_PATTERNS", "tests/,test/,testing/").split(",")
TEST_FILE_PATTERNS = os.getenv("TEST_FILE_PATTERNS", "test_*.py,*_test.py").split(",")
TEST_FUNCTION_PREFIXES = os.getenv("TEST_FUNCTION_PREFIXES", "test_").split(",")
TEST_CLASS_PATTERNS = os.getenv("TEST_CLASS_PATTERNS", "Test*,*Test").split(",")

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

## scanner.py

### 1. Update CodeAnalyzer Class Initialization

```python
def __init__(self, file_path, session, is_test_file=False):
    self.file_path = file_path
    self.session = session
    self.current_class = None
    self.current_function = None
    self.is_test_file = is_test_file
```

### 2. Update analyze_file Function

```python
def analyze_file(file_path, session, base_dir):
    # Skip standard library files
    if not is_project_file(file_path, base_dir):
        print(f"Skipping non-project file: {file_path}")
        return

    # Convert to relative path for storage
    rel_path = get_relative_path(file_path, base_dir)

    # Check if file is in tests directory
    is_test = is_test_file(rel_path)

    with open(file_path, "r", encoding="utf-8") as f:
        print(f"Analyzing file: {rel_path} (from {file_path})")
        try:
            tree = ast.parse(f.read(), filename=file_path)
            # Pass the test file flag to CodeAnalyzer
            analyzer = CodeAnalyzer(rel_path, session, is_test_file=is_test)
            analyzer.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {rel_path}: {e}")
        except UnicodeDecodeError:
            print(f"Unable to decode file: {rel_path} - skipping")
```

### 3. Update visit_ClassDef Method

```python
def visit_ClassDef(self, node):
    class_name = node.name
    line_num = getattr(node, 'lineno', -1)
    print(f"Visiting class: {class_name} in {self.file_path} at line {line_num}")
    self.current_class = class_name

    # Choose appropriate labels based on whether this is a test file
    if self.is_test_file:
        self.session.run(
            "MERGE (c:Class:Test:TestClass {name: $name, file: $file, line: $line, end_line: $end_line})",
            name=class_name,
            file=self.file_path,
            line=line_num,
            end_line=getattr(node, 'end_lineno', -1)
        )
    else:
        self.session.run(
            "MERGE (c:Class {name: $name, file: $file, line: $line, end_line: $end_line})",
            name=class_name,
            file=self.file_path,
            line=line_num,
            end_line=getattr(node, 'end_lineno', -1)
        )

    self.generic_visit(node)
    self.current_class = None
```

### 4. Update visit_FunctionDef Method

```python
def visit_FunctionDef(self, node):
    function_name = node.name

    # Skip special methods and private methods if desired
    if function_name.startswith('__') and function_name.endswith('__'):
        print(f"Skipping dunder method: {function_name} in {self.file_path}")
        return

    # Get line number information
    line_num = getattr(node, 'lineno', -1)
    end_line_num = getattr(node, 'end_lineno', -1)

    print(f"Visiting function: {function_name} in {self.file_path} at line {line_num}")
    full_name = f"{self.current_class}.{function_name}" if self.current_class else function_name
    self.current_function = full_name

    # Choose labels based on test file status and other conditions
    if self.is_test_file:
        labels = ":Function:Test:TestFunction"
    else:
        labels = ":Function"

    if function_name == "main":
        labels += ":MainFunction"
    if self.current_class:
        labels += ":ClassFunction"

    # Rest of the method remains the same...
```

### 5. Add Tracking of Imports (Phase 2)

```python
def visit_Import(self, node):
    for alias in node.names:
        imported_name = alias.name
        alias_name = alias.asname or imported_name

        if self.is_test_file:
            print(f"Import in test file: {imported_name} as {alias_name}")
            # Track imports for later analysis of test relationships
            self.session.run("""
                MERGE (i:Import {name: $name, alias: $alias, file: $file})
                WITH i
                MATCH (f:Function {name: $func_name, file: $file})
                MERGE (f)-[:IMPORTS]->(i)
            """, name=imported_name, alias=alias_name, file=self.file_path,
                func_name=self.current_function)

    self.generic_visit(node)

def visit_ImportFrom(self, node):
    module = node.module
    for alias in node.names:
        imported_name = alias.name
        alias_name = alias.asname or imported_name
        full_import = f"{module}.{imported_name}" if module else imported_name

        if self.is_test_file:
            print(f"ImportFrom in test file: {full_import} as {alias_name}")
            # Track imports for later analysis of test relationships
            self.session.run("""
                MERGE (i:Import {name: $name, module: $module, alias: $alias, file: $file})
                WITH i
                MATCH (f:Function {name: $func_name, file: $file})
                MERGE (f)-[:IMPORTS]->(i)
            """, name=imported_name, module=module, alias=alias_name,
                file=self.file_path, func_name=self.current_function)

    self.generic_visit(node)
```

### 6. Add Test Relationship Processing (Phase 2)

```python
def process_test_relationships(self):
    """
    Process relationships between test code and production code.
    Called at the end of analyze_file.
    """
    if not self.is_test_file:
        return

    # Process based on naming patterns
    self.session.run("""
        MATCH (test:TestFunction)
        WHERE test.name STARTS WITH 'test_'
        WITH test, substring(test.name, 5) AS tested_name
        MATCH (prod:Function)
        WHERE NOT prod:TestFunction AND prod.name = tested_name
        MERGE (test)-[:TESTS {method: 'naming_pattern'}]->(prod)
    """)

    # Process based on imports
    self.session.run("""
        MATCH (test:TestFunction)-[:IMPORTS]->(i:Import)
        MATCH (prod:Function)
        WHERE NOT prod:TestFunction AND prod.name = i.name
        MERGE (test)-[:TESTS {method: 'import'}]->(prod)
    """)

    # Process based on calls
    self.session.run("""
        MATCH (test:TestFunction)-[:CALLS]->(prod:Function)
        WHERE NOT prod:TestFunction
        MERGE (test)-[:TESTS {method: 'call'}]->(prod)
    """)
```

## codescan_mcp_server.py

### 1. Add Tool for Test Component Queries

```python
@mcp.tool()
def list_test_functions() -> List[Dict[str, Any]]:
    """
    List all test functions.

    Returns:
        List of test functions with their names, files, and line numbers
    """
    return q("""
        MATCH (f:TestFunction)
        RETURN f.name AS name, f.file AS file, f.line AS line, f.end_line AS end_line
        ORDER BY f.file, f.line
    """)

@mcp.tool()
def list_test_classes() -> List[Dict[str, Any]]:
    """
    List all test classes.

    Returns:
        List of test classes with their names, files, and line numbers
    """
    return q("""
        MATCH (c:TestClass)
        RETURN c.name AS name, c.file AS file, c.line AS line, c.end_line AS end_line
        ORDER BY c.file, c.line
    """)
```

### 2. Add Tools for Test Coverage Queries (Phase 2)

```python
@mcp.tool()
def untested_functions() -> List[Dict[str, Any]]:
    """
    List functions without tests.

    Returns:
        List of functions that don't have any tests covering them
    """
    return q("""
        MATCH (f:Function)
        WHERE NOT f:TestFunction
          AND NOT (:TestFunction)-[:TESTS]->(f)
        RETURN f.name AS name, f.file AS file, f.line AS line
        ORDER BY f.file, f.line
    """)

@mcp.tool()
def test_coverage_ratio() -> List[Dict[str, Any]]:
    """
    Get test coverage ratio.

    Returns:
        Overall test coverage ratio and counts
    """
    return q("""
        MATCH (f:Function) WHERE NOT f:TestFunction
        WITH count(f) AS total_functions
        MATCH (f:Function) WHERE NOT f:TestFunction
          AND (:TestFunction)-[:TESTS]->(f)
        WITH total_functions, count(f) AS tested_functions
        RETURN
            total_functions,
            tested_functions,
            CASE
                WHEN total_functions > 0 THEN toFloat(tested_functions) / total_functions
                ELSE 0
            END AS coverage_ratio
    """)
```

## Tests Required

1. **test_scanner.py**
   - Add tests to verify test labeling functionality
   - Add tests to verify test relationship detection

2. **test_neo4j_graph_queries.py**
   - Add tests for the new graph queries related to tests

3. **test_codescan_mcp_server.py**
   - Add tests for the new MCP tools related to tests
