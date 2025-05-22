# Migration to FastMCP with stdio Transport

This document outlines the plan and steps to migrate our custom `code_graph_http.py` (FastAPI with SSE) implementation to use the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) with `FastMCP` and `stdio` transport.

## 1. Motivation

Our current implementation uses FastAPI with Server-Sent Events (SSE) for the transport layer, with all JSON-RPC message construction and protocol details handled manually. This has led to several challenges:

- **Protocol Compatibility Issues**: Difficulty ensuring exact compliance with MCP client expectations, especially regarding the initial handshake.
- **Manual JSON-RPC Management**: Having to manually construct all JSON-RPC 2.0 messages and error objects.
- **Verbose Tool Definitions**: Explicit schema construction for each tool.
- **Complex Error Handling**: Managing errors across the protocol, transport, and tool execution layers.

Moving to the official SDK with `FastMCP` addresses these issues by:

- Using a protocol implementation maintained by the MCP team.
- Leveraging automatic schema generation from Python type hints and docstrings.
- Providing standardized error handling.
- Simplifying the codebase (~350 lines reduced to ~150 lines).

## 2. Architecture Comparison

### Current Architecture (FastAPI/SSE)

```
User Request → FastAPI/SSE → Custom JSON-RPC Handler → Neo4j Query → JSON-RPC Response
```

- **Transport**: HTTP with Server-Sent Events (SSE)
- **Protocol Handling**: Manual JSON-RPC 2.0 message construction
- **Tool Definition**: Explicit JSON schema creation
- **Error Handling**: Manual construction of JSON-RPC error objects

### Target Architecture (FastMCP/stdio)

```
User Request → MCP Client → stdio → FastMCP → Neo4j Query → FastMCP Response
```

- **Transport**: stdio (standard input/output)
- **Protocol Handling**: Handled by MCP SDK
- **Tool Definition**: Automatic from Python type hints and docstrings
- **Error Handling**: Standardized by FastMCP

## 3. Migration Steps

### 3.1 Project Setup

1. **Update Dependencies**:
   - Add `mcp[cli]` to `requirements.txt`
   - Remove `fastapi`, `uvicorn`, `sse-starlette` (unless needed for other components)
   - Keep `neo4j` and `python-dotenv`

2. **Create New Files**:
   - `codescan_mcp_server.py`: The new FastMCP server
   - `run_mcp_stdio_server.sh`: Shell script to run the server

### 3.2 Server Implementation

The new server will follow this structure:

```python
#!/usr/bin/env python3
"""
codescan_mcp_server.py - MCP Server using FastMCP and stdio.
Provides tools to query a Neo4j database populated with code analysis data.
"""
import os
import logging
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth
from mcp.server.fastmcp import FastMCP

# --- Configuration & Setup ---
load_dotenv(".env", override=True)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7600")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DEBUG_MCP = os.getenv("DEBUG_MCP", "false").lower() in ("true", "1", "yes")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MCP else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codescan_mcp_server")

# --- Neo4j Driver ---
driver = None
# Initialize driver...

# --- Initialize FastMCP ---
mcp = FastMCP("codescan_neo4j",
              description="Neo4j code graph analyzer for Python codebases",
              version="1.0.0")

# --- Query Helper ---
def q(cypher: str, **params) -> List[Dict[str, Any]]:
    # Neo4j query implementation...
    pass

# --- Tool Definitions ---
@mcp.tool()
def graph_summary() -> List[Dict[str, Any]]:
    """
    Get a summary of the code graph.
    Returns counts of functions, classes, and calls.
    """
    return q("""
        MATCH (f:Function) WITH count(f) AS funcs
        MATCH (c:Class)    WITH funcs, count(c) AS classes
        MATCH ()-[e:CALLS]->() RETURN funcs, classes, count(e) AS calls
    """)

# More tool definitions...

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting CodeScan MCP Server (FastMCP, stdio)")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
    finally:
        if driver:
            driver.close()
```

### 3.3 Tool Migration

For each tool, we'll convert from manually defined schemas to `@mcp.tool()` decorated functions with type hints and docstrings:

**Before (in code_graph_http.py):**
```python
def get_tool_definitions():
    return [
        {
            "name": "listFiles",
            "description": "List all files in the codebase",
            "inputSchema": {"type": "object", "properties": {}}
        },
        # ...more tool definitions...
    ]

def list_files(_):
    return q("MATCH (n) WHERE exists(n.file) RETURN DISTINCT n.file AS file ORDER BY file")
```

**After (in codescan_mcp_server.py):**
```python
@mcp.tool()
def list_files() -> List[Dict[str, Any]]:
    """
    List all unique file paths present in the code graph.
    """
    return q("MATCH (n) WHERE exists(n.file) RETURN DISTINCT n.file AS file ORDER BY file")
```

### 3.4 Run Script

Create a shell script to run the new MCP server:

```bash
#!/bin/bash
# Script to run the CodeScan MCP stdio server

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

echo "Starting CodeScan MCP Server (stdio)..."
# Execute the server script
python3 "${SCRIPT_DIR}/codescan_mcp_server.py"
```

Make it executable: `chmod +x run_mcp_stdio_server.sh`

## 4. Client Configuration

To use the new stdio-based server with MCP clients (e.g., Cursor):

### 4.1 Cursor Configuration

Update `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%AppData%\Claude\claude_desktop_config.json` (Windows):

```json
{
    "mcpServers": {
        "codescan_neo4j": {
            "command": "/absolute/path/to/your/project/run_mcp_stdio_server.sh",
            "args": [],
            "cwd": "/absolute/path/to/your/project"
        }
    }
}
```

### 4.2 Other MCP Clients

For clients using the MCP SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="/absolute/path/to/your/project/run_mcp_stdio_server.sh",
    args=[],
    env=None,
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Use tools...
            tools = await session.list_tools()
            result = await session.call_tool("graph_summary")
            print(result)
```

## 5. Testing

1. Run the new server directly: `./run_mcp_stdio_server.sh`
2. Check logs for successful startup and Neo4j connection
3. Using an MCP client (e.g., Cursor), test each tool:
   - `graph_summary`
   - `list_files`
   - `list_functions` with a file path argument
   - `list_classes` with a file path argument
   - `callees` with a function name argument
   - `callers` with a function name argument
   - `unresolved_references`
4. Verify error handling by providing invalid arguments

## 6. Deployment Considerations

- The current FastAPI server allows direct HTTP access and browser debugging
- The new stdio server is meant to be spawned by MCP clients
- If HTTP API access is still needed, consider:
  - Keeping a minimal HTTP API server separate from the MCP functionality
  - Wrapping the stdio server in a simple HTTP wrapper that forwards requests

## 7. Cleanup

Once the migration is complete and verified:

1. Rename `code_graph_http.py` to `code_graph_http.py.bak` or remove it
2. Update documentation to reflect the new architecture
3. Remove dependencies that are no longer needed

## 8. Implementation Status

The migration to FastMCP with stdio transport has been implemented with the following files:

1. **codescan_mcp_server.py**: The main MCP server implementation using FastMCP with the following features:
   - Configured Neo4j connection with error handling
   - Implemented all 7 tools using the `@mcp.tool()` decorator with type hints and docstrings:
     - `graph_summary()`
     - `list_files()`
     - `list_functions(file: str)`
     - `list_classes(file: str)`
     - `callees(fn: str)`
     - `callers(fn: str)`
     - `unresolved_references()`
   - Added proper error handling and logging
   - Ensured Neo4j driver cleanup on server exit

2. **run_mcp_stdio_server.sh**: A shell script to execute the server with stdio transport
   - Includes virtual environment activation
   - Properly sets script directory paths
   - Successfully tested to start the server

3. **requirements.txt**: Updated to include `mcp[cli]` and remove FastAPI-related dependencies

The implementation is complete and the server starts successfully with a connection to Neo4j. The next step is to configure an MCP client to use the server and test the individual tool functionality.

## References

- [MCP Python SDK Repository](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Quickstart for Server Developers](https://modelcontextprotocol.io/quickstart/server)
- [MCP Server Design Patterns and Learnings](./mcp_server_patterns.md)
