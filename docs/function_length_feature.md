# Function Length Feature

## Overview
The Function Length feature adds a new property to function nodes in the Neo4j database, which represents the number of lines that make up the function. This provides valuable information for codebase analysis, helping identify overly long functions that may need refactoring.

## Database Schema Update
Function nodes now include a `length` property:

```cypher
MERGE (f:Function {
    name: $name,
    file: $file,
    is_reference: false,
    line: $line,
    end_line: $end_line,
    length: $length  // New property
})
```

The `length` property is calculated as:
```
length = end_line - line + 1
```

Where:
- `line` is the starting line number of the function
- `end_line` is the ending line number of the function
- The `+1` ensures that single-line functions have a length of 1 (when start and end lines are the same)

## Usage

### Finding the Length of a Function

To query the length of a specific function:

```cypher
MATCH (f:Function {name: 'function_name'})
RETURN f.name, f.length
```

### Finding the Longest Functions

To find the longest functions in the codebase:

```cypher
MATCH (f:Function)
WHERE NOT f:ReferenceFunction
RETURN f.name, f.file, f.length
ORDER BY f.length DESC
LIMIT 10
```

### Finding Functions That Exceed a Certain Length

To find functions that exceed a certain length (e.g., 50 lines):

```cypher
MATCH (f:Function)
WHERE f.length > 50
RETURN f.name, f.file, f.length
ORDER BY f.length DESC
```

## Special Cases

1. **Reference Functions**: These are functions that are called but not defined in the analyzed codebase. They have a `length` value of 0.

2. **Edge Cases**: If the line numbers are not properly detected (e.g., if `line` or `end_line` is -1), the `length` will be set to 0.

## Future Enhancements

In the future, this feature could be extended to:

1. Add a similar `length` property to class nodes
2. Create MCP tools to find the longest functions in the codebase
3. Add length statistics to the graph summary
4. Visualize function lengths in Neo4j Browser with custom styling
