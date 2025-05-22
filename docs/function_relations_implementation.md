# Function Relations Implementation

This document outlines the implementation of the new tool `find_function_relations` which allows searching for function relations by function name with an option for partial matching.

## Background

Task #9 in the todo list required:
> Implement a tool to find functions relations by functions full name, it must have an option to search by partial name

This tool extends the existing functionality in the call graph module to allow more flexible searching of function relationships.

## Implementation Details

The tool was implemented in `codescan_lib/mcp_tools/call_graph.py` as a new function `find_function_relations`.

### Features

1. **Exact Matching**: By default, searches for a function with the exact name provided
2. **Partial Matching**: When `partial_match=True`, searches for functions containing the given substring
3. **Relationship Data**: For each matching function, returns:
   - Function details (name, file, line numbers)
   - Callers (functions that call the matched function)
   - Callees (functions called by the matched function)
4. **Result Limiting**: Default limit of 50 results per query to prevent overwhelming output

### Function Signature

```python
@mcp.tool()
def find_function_relations(function_name: str, partial_match: bool = False, limit: int = 50) -> Dict[str, Any]:
    """
    Find function relations by function name, with option to search by partial name.

    Args:
        function_name: Full or partial name of the function to find relations for
        partial_match: If True, will match functions containing the specified name substring
        limit: Maximum number of results to return (default: 50)

    Returns:
        Dictionary with matching functions, their callers, and callees
    """
```

### Return Structure

The function returns a dictionary with the following structure:

```python
{
    "matching_functions": [
        {
            "name": "function_name",
            "file": "path/to/file.py",
            "line": 10,
            "end_line": 20
        },
        # Additional matching functions...
    ],
    "relations": [
        {
            "function": {
                "name": "function_name",
                "file": "path/to/file.py",
                "line": 10,
                "end_line": 20
            },
            "callers": [
                {
                    "caller_name": "caller_function",
                    "caller_file": "path/to/caller.py"
                },
                # Additional callers...
            ],
            "callees": [
                {
                    "callee_name": "callee_function",
                    "callee_file": "path/to/callee.py"
                },
                # Additional callees...
            ]
        },
        # Relations for additional matching functions...
    ]
}
```

## Testing

Tests were added to `tests/test_new_tools.py` to verify the functionality:

1. `test_find_function_relations_exact_match`: Tests exact name matching
2. `test_find_function_relations_partial_match`: Tests partial name matching
3. `test_find_function_relations_no_matches`: Tests behavior when no matches are found

## Usage Examples

### Find relations for a specific function by exact name:

```python
relations = find_function_relations("process_data")
```

### Find relations for functions containing a substring:

```python
relations = find_function_relations("process", partial_match=True)
```

### Limit the number of results:

```python
relations = find_function_relations("init", partial_match=True, limit=10)
```

## Next Steps

The completed implementation satisfies task #9. The next related task (#10) is to implement a similar tool for class relations.
