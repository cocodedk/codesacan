# Function Length Implementation Tasks

## Task List

### Code Changes
- [x] Modify `visit_FunctionDef` in `analyzer.py` to calculate function length
- [x] Add `length` property to function node creation query
- [x] Handle edge case for reference functions (no end_line or end_line == -1)

### Testing
- [x] Create test file with functions of various lengths
- [x] Write test to verify function length is correctly calculated and stored
- [x] Test edge cases (single-line functions, reference functions)

### Documentation
- [x] Update documentation to include information about the new `length` property
- [x] Document how to query for function length in Neo4j

### Future Enhancements (not in current scope)
- [ ] Add similar length calculation for class nodes
- [ ] Create MCP tool to find longest functions
- [ ] Add length statistics to graph summary
