# New Tools Implementation Plan

## Requirements

We need to implement three new tools as specified in the `tasks/todo.md` file:

1. `untested_classes`: List classes without tests
2. `transitive_calls`: Find full relationship chains between two functions (if one call will eventually lead to the other)
3. `functions_without_tests`: This already exists as `untested_functions` but we'll review it for completeness

## Implementation Approach

### 1. `untested_classes`
- Similar to the existing `untested_functions` tool
- Query Neo4j for classes that don't have test relationships
- Return class name, file, and line number

### 2. `transitive_calls`
- Use Neo4j's transitive relationship capabilities to find paths from one function to another
- Allow specifying depth limit (optional parameter)
- Return full path information including intermediate functions

### 3. Verify `untested_functions`
- The existing implementation already covers the requirement
- No need to create a new tool for this

## Testing Plan

1. Create test cases for each new tool:
   - Test untested_classes with known untested classes
   - Test transitive_calls with known function call chains

2. Integration testing:
   - Test tools with the MCP server interface

## Implementation Steps

1. Implement the Cypher queries for each tool
2. Add the tool definitions to the MCP server
3. Test each tool with valid inputs
4. Add documentation for the new tools
