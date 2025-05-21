# FastMCP Migration Tasks

This document lists the specific tasks required to migrate our custom FastAPI/SSE MCP server to the official Python SDK with FastMCP and stdio transport.

## Project Setup

- [x] Add `mcp[cli]` to `requirements.txt`
- [x] Remove `fastapi`, `uvicorn`, `sse-starlette` from `requirements.txt` (unless needed for other components)
- [x] Install updated dependencies (`pip install -r requirements.txt` or `uv pip install -r requirements.txt`)
- [x] Create skeleton files:
  - [x] `codescan_mcp_server.py`
  - [x] `run_mcp_stdio_server.sh`

## `codescan_mcp_server.py` Implementation

### Basic Structure

- [x] Add shebang and module docstring
- [x] Import necessary libraries (`os`, `logging`, `typing`, `dotenv`, `neo4j`, `mcp.server.fastmcp`)
- [x] Setup environment variables from `.env`
- [x] Configure logging with appropriate format and level
- [x] Create `logger` instance
- [x] Initialize FastMCP instance with server name and metadata

### Neo4j Connection

- [x] Initialize global Neo4j driver with environment variables
- [x] Add error handling for Neo4j connection failures
- [x] Implement `q` helper function for Neo4j queries with proper error handling
- [x] Ensure driver cleanup in program exit

### Tool Implementations

- [x] Implement `@mcp.tool()` decorated function for `graph_summary`
  - [x] Add proper docstring
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `list_files`
  - [x] Add proper docstring
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `list_functions`
  - [x] Add proper docstring
  - [x] Add parameter type annotation
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `list_classes`
  - [x] Add proper docstring
  - [x] Add parameter type annotation
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `callees`
  - [x] Add proper docstring
  - [x] Add parameter type annotation
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `callers`
  - [x] Add proper docstring
  - [x] Add parameter type annotation
  - [x] Add return type annotation
  - [x] Implement with Neo4j query
- [x] Implement `@mcp.tool()` decorated function for `unresolved_references`
  - [x] Add proper docstring
  - [x] Add return type annotation
  - [x] Implement with Neo4j query

### Main Execution

- [x] Add `if __name__ == "__main__"` block
- [x] Log server startup
- [x] Call `mcp.run(transport='stdio')` in try/except block
- [x] Add appropriate error handling
- [x] Add Neo4j driver cleanup in `finally` block

## `run_mcp_stdio_server.sh` Implementation

- [x] Add shebang line
- [x] Add comments and echo statements for clarity
- [x] Get script directory for relative paths
- [x] Add python command to run the server script
- [x] Make script executable with `chmod +x run_mcp_stdio_server.sh`

## Testing

- [x] Run server directly to verify it starts without errors
- [x] Check Neo4j connection is working
- [ ] Configure an MCP client to use the server:
  - For Cursor: Update `claude_desktop_config.json` with server config
  - Or use a Python MCP client script for testing
- [ ] Test each tool:
  - [ ] `graph_summary`
  - [ ] `list_files`
  - [ ] `list_functions` with valid file path
  - [ ] `list_functions` with invalid file path (error handling)
  - [ ] `list_classes` with valid file path
  - [ ] `list_classes` with invalid file path (error handling)
  - [ ] `callees` with valid function name
  - [ ] `callees` with invalid function name (error handling)
  - [ ] `callers` with valid function name
  - [ ] `callers` with invalid function name (error handling)
  - [ ] `unresolved_references`

## Documentation

- [ ] Add comments in code explaining key components
- [ ] Update main `README.md` with information about the new server
- [ ] Document how to configure clients to use the new server
- [ ] Add requirements and setup instructions

## Deployment

- [ ] Test the server in the deployment environment
- [ ] Update any deployment scripts/configurations
- [ ] If HTTP access is still needed:
  - [ ] Determine approach (separate minimal HTTP API or wrapper)
  - [ ] Implement chosen approach

## Cleanup

- [ ] Rename `code_graph_http.py` to `code_graph_http.py.bak` or remove it
- [ ] Remove old server startup scripts if no longer needed
- [ ] Remove any other obsolete files or code
- [ ] Perform final review to ensure nothing is missed
