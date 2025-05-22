# Test Coverage Visualization

This document describes how to visualize and analyze test coverage in your codebase using CodeScan and Neo4j.

## Overview

CodeScan identifies test components and establishes `TESTS` relationships between test functions and the production code they test. This allows you to visualize your test coverage and identify untested code.

## Neo4j Browser Visualization

### Accessing Neo4j Browser

1. Start your Neo4j database (typically with Docker Compose)
2. Open Neo4j Browser at `http://localhost:7400` (or your configured port)
3. Login with your credentials (default: neo4j/password)

### Visualizing Test Coverage

Here are some useful Cypher queries to visualize test coverage:

#### 1. Test Functions and What They Test

```cypher
MATCH (test:TestFunction)-[r:TESTS]->(prod:Function)
RETURN test, r, prod
LIMIT 25
```

This query shows test functions and the production functions they test, with a `TESTS` relationship between them. The relationship includes a `method` property showing how the relationship was detected (naming_pattern, import, or call).

#### 2. Color-Coded Function Status

```cypher
MATCH (f:Function)
WHERE NOT f:TestFunction
WITH f
OPTIONAL MATCH (test:TestFunction)-[:TESTS]->(f)
RETURN f,
       CASE WHEN test IS NOT NULL THEN "Tested" ELSE "Untested" END AS status
```

In Neo4j Browser, you can customize the styling to color-code functions based on their test status:

1. Click the "Style" button in the visualization panel
2. Add a new rule: `node.status = "Untested"`
3. Set the color to red
4. Add another rule: `node.status = "Tested"`
5. Set the color to green

#### 3. Test Coverage Heatmap

```cypher
MATCH (f:Function)
WHERE NOT f:TestFunction
WITH f.file AS file, count(f) AS total
OPTIONAL MATCH (f:Function)<-[:TESTS]-(:TestFunction)
WHERE f.file = file
WITH file, total, count(f) AS tested
RETURN file, total, tested,
       toFloat(tested)/total AS coverage
ORDER BY coverage DESC
```

This query shows test coverage percentages for each file in your codebase.

## MCP Tools for Test Coverage

CodeScan MCP provides several tools for analyzing test coverage:

### Listing Test Components

```python
# List all test functions
test_functions = codescan.list_test_functions()

# List all test classes
test_classes = codescan.list_test_classes()

# Get all test files
test_files = codescan.get_test_files()
```

### Analyzing Test Coverage

```python
# Get functions without tests
untested = codescan.untested_functions()

# Get overall test coverage ratio
coverage = codescan.test_coverage_ratio()
```

### Tracing Test Relationships

```python
# Find which functions are tested by a specific test file
tested_by_file = codescan.functions_tested_by("tests/test_calculator.py")

# Find which tests cover a specific function
tests_for_function = codescan.tests_for_function("add", "calculator.py")
```

## Visualization Tips

### Coloring Nodes by Test Status

In Neo4j Browser, you can use styling to highlight untested functions:

1. Run a query that returns untested functions with a label
2. In the Style panel, set the color based on the label
3. Save the styling as a favorite for future use

### Creating Coverage Reports

You can generate test coverage reports using CodeScan MCP:

```python
import matplotlib.pyplot as plt

# Get coverage data
coverage = codescan.test_coverage_ratio()[0]
total = coverage["total_functions"]
tested = coverage["tested_functions"]
ratio = coverage["coverage_ratio"]

# Plot as pie chart
labels = ['Tested', 'Untested']
sizes = [tested, total-tested]
colors = ['green', 'red']

plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
plt.axis('equal')
plt.title('Test Coverage')
plt.savefig('test_coverage.png')
```

## Practical Examples

### Identifying Critical Untested Functions

Find important functions without tests (those called by many other functions):

```cypher
MATCH (f:Function)
WHERE NOT f:TestFunction AND NOT (:TestFunction)-[:TESTS]->(f)
WITH f
MATCH (caller:Function)-[:CALLS]->(f)
WITH f, count(caller) AS callers
WHERE callers > 2
RETURN f.name, f.file, callers
ORDER BY callers DESC
```

### Finding Test-Dense Areas

Identify areas of your codebase with high test coverage:

```cypher
MATCH (f:Function)
WHERE NOT f:TestFunction
WITH f.file AS file, count(f) AS total
WHERE total > 5
MATCH (f:Function)<-[:TESTS]-(:TestFunction)
WHERE f.file = file
WITH file, total, count(DISTINCT f) AS tested
WHERE toFloat(tested)/total > 0.8
RETURN file, total, tested, toFloat(tested)/total AS coverage
ORDER BY coverage DESC
```

This query finds files with more than 80% test coverage that have at least 5 functions.
