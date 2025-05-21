# CodeScan: Python Code Analysis with Neo4j Graph Visualization

## Product Overview

CodeScan is a static code analysis tool that scans Python codebases, extracts structural information and call relationships, and stores this data in a Neo4j graph database for advanced visualization and exploration. It provides integration with the Cursor IDE through the Model Context Protocol (MCP), enabling AI-assisted code exploration.

## Key Components

### 1. Python Code Scanner (`scanner.py`)

The scanner component traverses Python source files, extracting:
- Class definitions and their locations
- Function definitions with line numbers
- Call relationships between functions
- Arguments passed in function calls

All extracted information is stored in a Neo4j graph database, creating a comprehensive representation of the codebase structure and relationships.

### 2. MCP-Compatible API Server (`code_graph_http.py`)

The API server exposes the Neo4j graph data through:
- A FastAPI server with Server-Sent Events (SSE) support
- Full implementation of the Model Context Protocol (MCP)
- RESTful endpoints for querying the code graph
- Health check and connection management

## How It Works

1. **Code Scanning**: The scanner traverses Python source files, using AST (Abstract Syntax Tree) analysis to identify classes, functions, and call relationships.

2. **Graph Construction**: Extracted elements are stored in Neo4j as nodes and relationships:
   - Classes are represented as `:Class` nodes
   - Functions are represented as `:Function` nodes with additional labels (`:MainFunction`, `:ClassFunction`, `:ReferenceFunction`)
   - Calls between functions are represented as `:CALLS` relationships
   - Class membership is represented as `:CONTAINS` relationships

3. **Visualization**: The Neo4j Browser with GraSS styling provides an interactive visualization of the code structure.

4. **MCP Integration**: The API server implements the Model Context Protocol, allowing Cursor IDE to query and explore the code graph through natural language via Claude.

## Key Features

### Code Structure Analysis
- Extract classes, functions, and their relationships
- Track line numbers for precise code location
- Handle reference functions (called but not yet defined)
- Colorize different node types for better visualization

### Advanced Querying
- Find all callers of a specific function
- List all functions in a file
- Discover unresolved function references
- Generate summary statistics of the codebase

### MCP Protocol Support
- Full compatibility with Cursor's Model Context Protocol
- Expose code graph as tools to Claude and other MCP clients
- Streaming results via Server-Sent Events (SSE)
- Support for both GET and POST requests

## Technical Requirements

### System Requirements
- Python 3.8+
- Neo4j 5.x database (Docker recommended)
- Docker and Docker Compose (for Neo4j container)

### Dependencies
- neo4j-python-driver: Connection to Neo4j database
- fastapi & uvicorn: API server implementation
- python-dotenv: Environment configuration
- sse-starlette: Server-Sent Events support

## Setup & Usage

### Installation
1. Clone the repository
2. Run `install.sh` to create a Python virtual environment and install dependencies
3. Start Neo4j using Docker Compose
4. Configure connection settings in `.env`

### Running
1. Execute `scanner.py` to analyze your codebase and populate the Neo4j database
2. Run `code_graph_http.py` to start the MCP-compatible API server
3. Connect to the server from Cursor IDE or other MCP clients

## Integration with Cursor IDE

CodeScan implements the Model Context Protocol (MCP), allowing seamless integration with Cursor IDE. This enables:

1. **AI-Powered Code Exploration**: Ask questions about your codebase in natural language
2. **Relationship Discovery**: Find connections between different parts of your code
3. **Contextual Understanding**: Provide Claude with structural context about your codebase

## Security Considerations

- The tool only performs read operations on your codebase
- Neo4j connection details are stored in environment variables
- CORS validation is implemented for API requests
- The scanner never executes code, only analyzes its structure

## Future Enhancements

- Support for additional programming languages
- More advanced static analysis features
- Enhanced visualization options
- Performance optimizations for large codebases
