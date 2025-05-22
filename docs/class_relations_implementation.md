# Class Relations Implementation

This document outlines the implementation of the new tool `find_class_relations` which allows searching for class relations by class name with an option for partial matching.

## Background

Task #10 in the todo list required:
> Implement a tool to find classes relations by classes full name, it must have an option to search by partial name

This tool extends the existing functionality in the class tools module to allow more flexible searching of class relationships.

## Implementation Details

The tool was implemented in `codescan_lib/mcp_tools/class_tools.py` as a new function `find_class_relations`.

### Features

1. **Exact Matching**: By default, searches for a class with the exact name provided
2. **Partial Matching**: When `partial_match=True`, searches for classes containing the given substring
3. **Relationship Data**: For each matching class, returns:
   - Class details (name, file, line numbers)
   - Methods contained in the class
   - File information that contains the class
   - Related classes that share similar method names
4. **Result Limiting**: Default limit of 50 results per query to prevent overwhelming output

### Function Signature

```python
@mcp.tool()
def find_class_relations(class_name: str, partial_match: bool = False, limit: int = 50) -> Dict[str, Any]:
    """
    Find class relations by class name, with option to search by partial name.

    Args:
        class_name: Full or partial name of the class to find relations for
        partial_match: If True, will match classes containing the specified name substring
        limit: Maximum number of results to return (default: 50)

    Returns:
        Dictionary with matching classes, their methods, and containing files
    """
```

### Return Structure

The function returns a dictionary with the following structure:

```python
{
    "matching_classes": [
        {
            "name": "ClassName",
            "file": "path/to/file.py",
            "line": 10,
            "end_line": 50
        },
        # Additional matching classes...
    ],
    "relations": [
        {
            "class": {
                "name": "ClassName",
                "file": "path/to/file.py",
                "line": 10,
                "end_line": 50
            },
            "methods": [
                {
                    "method_name": "ClassName.method_name",
                    "method_line": 15,
                    "method_end_line": 20,
                    "method_length": 6
                },
                # Additional methods...
            ],
            "file": {
                "file_path": "path/to/file.py",
                "file_type": "production",
                "is_test_file": false,
                "is_example_file": false
            },
            "related_classes": [
                {
                    "related_class_name": "RelatedClass",
                    "related_class_file": "path/to/related.py",
                    "shared_methods": 1
                },
                # Additional related classes...
            ]
        },
        # Relations for additional matching classes...
    ]
}
```

## Testing

Tests were added to `tests/test_new_tools.py` to verify the functionality:

1. `test_find_class_relations_exact_match`: Tests exact name matching
2. `test_find_class_relations_partial_match`: Tests partial name matching
3. `test_find_class_relations_no_matches`: Tests behavior when no matches are found

## Usage Examples

### Find relations for a specific class by exact name:

```python
relations = find_class_relations("UserAccount")
```

### Find relations for classes containing a substring:

```python
relations = find_class_relations("Account", partial_match=True)
```

### Limit the number of results:

```python
relations = find_class_relations("Test", partial_match=True, limit=10)
```

## Class Relationships

In the CodeScan codebase, the following class relationships are tracked:

1. **Class-Method Relationship**: Classes contain methods, represented by the `CONTAINS` relationship from a `Class` node to a `Function` node.
2. **File-Class Relationship**: Files contain classes, represented by the `CONTAINS` relationship from a `File` node to a `Class` node.
3. **Related Classes**: Classes that share similar method names are identified as potentially related, though they aren't explicitly linked in the database.

## Next Steps

The implementation successfully completes task #10 from the todo list. Future enhancements could include:

1. Adding more class relationship types, such as inheritance relationships
2. Improving the detection of related classes by considering method signatures and parameter types
3. Adding visualization tools for class hierarchies and relationships
