# Function Length Implementation Plan

## Overview
This document outlines the plan for implementing function length tracking in the Neo4j database for the code analyzer. The goal is to add a `length` property to function nodes that represents the number of lines in the function.

## Requirements
1. Calculate the length of functions (number of lines) during code analysis
2. Store the length as a property on function nodes in the Neo4j database
3. Ensure the length calculation is accurate for various function formats
4. Create tests to verify the length calculation

## Implementation Details

### Length Calculation
The function length will be calculated as:
```
length = end_line - line + 1
```
Where:
- `line` is the starting line number of the function
- `end_line` is the ending line number of the function
- The `+1` ensures that single-line functions have a length of 1 (when start and end lines are the same)

### Edge Cases
1. Reference functions: These functions don't have an `end_line` set (or it might be set to -1). In this case, the length should be set to 0.
2. Invalid line numbers: If either `line` or `end_line` is -1 or otherwise invalid, we'll need to handle this appropriately.

### Neo4j Schema Update
The function node schema will be updated to include a `length` property:
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

## Testing Strategy
1. Create test functions with known line counts
2. Analyze these functions using the modified analyzer
3. Verify that the `length` property is correctly set
4. Test edge cases (single-line functions, reference functions)

## Future Considerations
1. Add similar length calculation for class nodes
2. Create MCP tools to find long functions (potential code smells)
3. Add size metrics to the graph summary tool
