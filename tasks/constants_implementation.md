# Constants Implementation Tasks

## Task List

### Database Schema Updates
- [x] Update `clear_database` to handle Constant nodes

### CodeAnalyzer Extension
- [x] Add constant detection to `CodeAnalyzer` class
- [x] Implement module-level constant detection
- [x] Implement class-level constant detection
- [x] Implement function-level constant detection
- [x] Add methods to create Constant nodes in Neo4j
- [x] Add relationships between constants and their containers

### Constant Detection Logic
- [x] Define constant naming pattern recognition
- [x] Implement value extraction for different constant types
- [x] Add handling for collections and complex constants
- [x] Store constant type information

### Integration Testing
- [x] Create test files with various constants
- [x] Write tests to verify constant detection
- [x] Test nested constant scopes (module > class > function)

### Repetitive Constants Tool
- [x] Create Neo4j query to find duplicate constant values
- [x] Implement MCP tool for finding repetitive constants
- [x] Add documentation for the new tool
