# Test Labeling and Coverage Detection Tasks

## Phase 1: Test Component Labeling

- [x] Add configuration variables for test patterns (directories, files, functions, classes)
- [x] Create a flexible `is_test_file` detection function that works across different repo structures
- [x] Modify `analyze_file` in scanner.py to use the configurable test detection
- [x] Add is_test_file parameter to CodeAnalyzer class
- [x] Update `visit_ClassDef` to add Test and TestClass labels for test classes
- [x] Update `visit_FunctionDef` to add Test and TestFunction labels for test functions
- [x] Add command-line options to customize test detection patterns
- [x] Add environment variable support for test detection configuration
- [x] Add tests to verify correct labeling of test components
- [x] Add MCP server tools to query for test components

## Phase 2: Test Coverage Detection

- [x] Define TESTS relationship type with appropriate properties
- [x] Implement naming pattern detection for test functions and classes with configurable patterns
- [x] Add `visit_Import` and `visit_ImportFrom` methods to track imports in test files
- [x] Enhance call tracking to identify test-to-production code calls
- [x] Create TESTS relationships based on naming, imports, and calls
- [x] Add tests to verify correct test coverage detection
- [x] Add MCP server tools to query test coverage

## Phase 3: Testing and Documentation

- [ ] Write integration tests for test labeling with different repo structures
- [ ] Write integration tests for test coverage detection with different naming conventions
- [ ] Update README.md with new features
- [ ] Document configuration options for different repository structures
- [ ] Create documentation for test coverage visualization
- [ ] Update user guide with examples of test coverage queries
