# Example Labeling and Detection

This document describes how CodeScan identifies and labels example code components in the codebase.

## Overview

In many codebases, examples are provided to demonstrate how to use the codebase. These examples are not intended to be part of the production code, nor are they tests. CodeScan now distinguishes these components with special labels.

## Example Detection

CodeScan automatically detects examples based on the following criteria:

- Files located in directories named `examples/`
- Special labeling for classes and functions in example files:
  - Classes are labeled with `:Example` and `:ExampleClass`
  - Functions are labeled with `:Example` and `:ExampleFunction`

## MCP Tools for Example Analysis

The following MCP tools are available for analyzing examples:

### 1. List Example Functions

```python
@mcp.tool()
def list_example_functions():
    """
    List all example functions.

    Returns:
        List of example functions with their names, files, and line numbers
    """
```

### 2. List Example Classes

```python
@mcp.tool()
def list_example_classes():
    """
    List all example classes.

    Returns:
        List of example classes with their names, files, and line numbers
    """
```

### 3. Get Example Files

```python
@mcp.tool()
def get_example_files():
    """
    List all files containing examples.

    Returns:
        List of file paths containing example components
    """
```

## Neo4j Queries for Examples

You can use the following Cypher queries in the Neo4j browser to explore examples:

### Find all example components
```cypher
MATCH (n:Example)
RETURN n
```

### Find all example classes
```cypher
MATCH (c:ExampleClass)
RETURN c
```

### Find all example functions
```cypher
MATCH (f:ExampleFunction)
RETURN f
```

### Find relationships between examples and production code
```cypher
MATCH (e:Example)-[r]->(n)
WHERE NOT n:Example
RETURN e, r, n
```

## Example File Visualization

Examples appear in the Neo4j browser visualization with distinct labels, making it easy to distinguish them from both production code and test code.

## Benefits

- Clear separation between examples, tests, and production code
- Ability to exclude examples from analysis when desired
- Better understanding of the purpose of different code components
- Improved visualization and categorization in Neo4j browser
