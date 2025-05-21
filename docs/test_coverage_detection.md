# Test Coverage Detection

This document outlines an approach to detect if classes or functions have associated tests in the codebase.

## Overview

A critical part of code quality analysis is understanding which parts of the codebase are covered by tests. In a graph-based code analysis system, we can leverage relationships between code nodes to determine test coverage.

## Detection Approach

There are several heuristics that can be used to detect relationships between production code and test code:

### 1. Naming Conventions

Most test frameworks follow naming conventions that indicate which code is being tested:

- Test classes are often named after the class they test with a `Test` prefix or suffix (e.g., `TestScanner` tests `Scanner`)
- Test functions often have the name of the function being tested in their own name (e.g., `test_analyze_file` tests `analyze_file`)

### 2. Import Analysis

Tests typically import the modules, classes, or functions they are testing:

- By analyzing import statements in test files, we can create direct links to the tested components
- This creates an explicit `TESTS` relationship from test code to production code

### 3. Call Analysis

Test functions often call the functions they are testing:

- When a test function calls a production function, it indicates a testing relationship
- These call patterns can be used to create `TESTS` relationships

## Proposed Implementation

To implement test coverage detection, we should:

1. Create a new relationship type `TESTS` in the Neo4j graph
2. Enhance the code analyzer to identify potential test relationships
3. For each test function/class, try to establish which production components it tests

### Implementation Steps

1. **Naming Pattern Matching**:
   - For each `TestFunction`, check if its name includes the name of a production function
   - For each `TestClass`, check if its name is a prefix/suffix variant of a production class

2. **Import Tracking**:
   - Track imports in test files to establish direct connections to production code
   - Add a new `visit_Import` method to the code analyzer

3. **Call Graph Analysis**:
   - If a test function calls a production function, establish a testing relationship
   - Enhance the existing call tracking to identify test-to-production calls

## Example Query

Once implemented, test coverage could be queried with:

```cypher
// Find functions without tests
MATCH (f:Function)
WHERE NOT f:TestFunction
  AND NOT (:TestFunction)-[:TESTS]->(f)
RETURN f.name, f.file, f.line
ORDER BY f.file, f.line
```

This would identify production functions that lack dedicated tests.
