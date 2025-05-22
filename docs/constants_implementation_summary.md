# Constants Implementation Summary

## Overview
This document summarizes the implementation of constant detection, storage in the Neo4j database, and the tool to find repetitive constants across the codebase.

## Features Implemented

### 1. Constant Detection
- Added constant detection to the `CodeAnalyzer` class in `analyzer.py`
- Constants are identified by all-uppercase names with underscores (e.g., `MAX_RETRY_COUNT`)
- The analyzer detects constants at module, class, and function scope levels
- Handles various types of constants: strings, numbers, booleans, lists, dictionaries, tuples, etc.

### 2. Database Storage
- Added a new `:Constant` node type to represent constants in the code
- Constants are stored with metadata:
  - `name`: Name of the constant
  - `value`: String representation of the constant's value
  - `type`: Type of the constant (str, int, float, bool, list, dict, etc.)
  - `file`: File path where the constant is defined
  - `line`: Line number where the constant is defined
  - `end_line`: End line number for multi-line constants
  - `scope`: Scope of the constant (module, class, function)
- Added `:DEFINES` relationships between containers (classes/functions) and constants

### 3. Repetitive Constants Tool
- Added a `repetitive_constants` MCP tool in `codescan_mcp_server.py`
- The tool finds constants with the same value used in multiple places across the codebase
- Returns information about the value, type, count, and locations of repetitive constants
- Helps identify potential code duplication and candidates for refactoring

## Usage

### Finding Constants
After scanning the codebase, constant nodes can be found in the Neo4j database using Cypher queries:

```cypher
// Find all constants
MATCH (c:Constant) RETURN c

// Find constants in a specific file
MATCH (c:Constant {file: "path/to/file.py"}) RETURN c

// Find constants of a specific type
MATCH (c:Constant {type: "str"}) RETURN c
```

### Finding Repetitive Constants
Use the `repetitive_constants` MCP tool to find constants with the same value used in multiple places:

```python
from codescan_mcp_server import repetitive_constants

# Get all repetitive constants (default limit: 10)
result = repetitive_constants()

# Get top 5 repetitive constants
result = repetitive_constants(limit=5)
```

## Future Improvements

1. **Constant Value Equivalence**: Implement semantic equivalence for constants with different representations but the same effective value (e.g., `3.0` and `3`)
2. **Constant Usage Tracking**: Track where constants are used across the codebase
3. **Refactoring Suggestions**: Suggest locations where constants should be consolidated or moved to a central constants file
4. **Support for More Languages**: Extend constant detection to other programming languages
