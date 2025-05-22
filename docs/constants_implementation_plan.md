# Constants Implementation Plan

## Overview
This plan outlines the steps to implement constant detection, storage in the Neo4j database, and a tool to find repetitive constants in the code.

## Requirements
1. Detect constants in Python code (variables defined with uppercase names and assigned a literal value)
2. Store constants in the Neo4j database with appropriate metadata
3. Create a tool to find repetitive constants across the codebase

## Implementation Steps

### 1. Update Database Schema
- Add a new `:Constant` node type to represent constants in the code
- Store metadata such as name, value, file, line number, and type
- Create `:DEFINES` relationships between files/functions/classes and constants

### 2. Extend Code Analyzer
- Modify `CodeAnalyzer` in `analyzer.py` to detect constant definitions
- Add methods to detect constants in module-level, class-level, and function-level scopes
- Store constants in the Neo4j database

### 3. Add Constant Detection Logic
- Identify constants using naming conventions (all uppercase with underscores)
- Capture constant values, types, and locations
- Handle different types of constants (strings, numbers, booleans, lists, etc.)

### 4. Add Tool to Find Repetitive Constants
- Create a new Neo4j query to find identical constant values used in multiple places
- Implement MCP tool to expose this functionality
- Return a list of repetitive constants with their locations

## Database Schema

### Nodes
- `:Constant` - Represents a constant in the code
  - `name`: Name of the constant (e.g., "MAX_RETRY_COUNT")
  - `value`: String representation of the constant's value
  - `type`: Type of the constant (string, int, float, bool, list, dict, etc.)
  - `file`: File path where the constant is defined
  - `line`: Line number where the constant is defined
  - `end_line`: End line number for multi-line constants
  - `scope`: Scope of the constant (module, class, function)

### Relationships
- `:DEFINES` - Connects a file, class, or function to a constant it defines
  - `color`: Color for visualization (#E91E63) - Pink for defines relationships

## Testing Strategy
1. Create test files with various constants at different scopes
2. Verify constants are detected and stored correctly
3. Test the repetitive constants tool with known duplicate values
