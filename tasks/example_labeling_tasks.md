# Example Labeling Tasks

## Implementation Tasks

- [x] Create an `is_example_file` function to detect files in the examples directory
- [x] Modify the `CodeAnalyzer` class to track if a file is an example file
- [x] Update the `visit_ClassDef` method to add Example and ExampleClass labels
- [x] Update the `visit_FunctionDef` method to add Example and ExampleFunction labels
- [x] Update the `analyze_file` function to detect example files and print appropriate messages
- [x] Fix examples detection for paths with different directory separators

## Testing Tasks

- [x] Create `test_example_labeling.py` to verify example detection and labeling
- [x] Add test cases for `is_example_file` function
- [x] Add test cases for class labeling in example files
- [x] Add test cases for function labeling in example files
- [x] Add test cases to verify regular files don't get example labels

## Documentation Tasks

- [x] Create documentation in `docs/example_labeling.md`
- [x] Document MCP tools for querying example components
- [x] Document Neo4j queries for exploring examples

## MCP Tool Implementation Tasks

- [x] Add `list_example_functions` MCP tool
- [x] Add `list_example_classes` MCP tool
- [x] Add `get_example_files` MCP tool
