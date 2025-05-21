#!/usr/bin/env python3
"""
code_graph_http.py

FastAPI + SSE server that implements Cursor's Model Context Protocol (MCP)
for querying the Neo4j code-graph created by scanner.py.  Read-only: it never
runs the scanner—only answers Cypher queries.

Dependencies
------------
pip install fastapi uvicorn sse-starlette neo4j python-dotenv

Environment (.env)
------------------
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=demodemo
ALLOWED_ORIGINS=http://localhost,https://app.cursor.sh       # optional
"""

import asyncio, json, os, signal, logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth

# ---------------------------------------------------------------------------
# ENV & CONFIG
# ---------------------------------------------------------------------------

load_dotenv(".env", override=True)

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7600")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "demodemo")
ALLOWED_ORIGINS = set(
    [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:*,https://app.cursor.sh,null").split(",") if o.strip()]
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

driver = None
try:
    # Create Neo4j driver (synchronous version)
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_lifetime=300,
        connection_timeout=20,
    )
    # Test connection
    with driver.session() as session:
        session.run("RETURN 1 AS ok")
    logging.info(f"Successfully connected to Neo4j at {NEO4J_URI}")
except Exception as e:
    logging.error(f"Failed to connect to Neo4j: {e}")
    # Keep driver as None - will be checked in health endpoint

# ---------------------------------------------------------------------------
# CYTHER HELPERS
# ---------------------------------------------------------------------------

def q(cypher: str, **params) -> list[Dict[str, Any]]:
    """Run a Cypher query and return list of dicts."""
    if driver is None:
        logging.error("Neo4j driver not initialized, cannot run query")
        return []

    try:
        with driver.session() as s:
            return [r.data() for r in s.run(cypher, **params)]
    except Exception as e:
        logging.error(f"Neo4j query error: {e}")
        return []

def graph_summary(_):
    return q("""
        MATCH (f:Function) WITH count(f) AS funcs
        MATCH (c:Class)    WITH funcs, count(c) AS classes
        MATCH ()-[e:CALLS]->() RETURN funcs, classes, count(e) AS calls
    """)

def list_files(_):
    return q("MATCH (n) WHERE exists(n.file) RETURN DISTINCT n.file AS file ORDER BY file")

def list_filepaths(_):     # alias kept for clarity
    return list_files({})

def list_functions(params):
    return q("""
        MATCH (f:Function {file:$file})
        WHERE coalesce(f.is_reference,false)=false
        RETURN f.name AS name, f.line AS line, f.end_line AS end_line
        ORDER BY f.line
    """, file=params["file"])

def list_classes(params):
    return q("""
        MATCH (c:Class {file:$file})
        RETURN c.name AS class, c.line AS line, c.end_line AS end_line
        ORDER BY c.line
    """, file=params["file"])

def callees(params):
    return q("""
        MATCH (caller:Function {name:$fn})-[:CALLS]->(callee:Function)
        RETURN callee.name AS callee, caller.file AS caller_file
    """, fn=params["fn"])

def callers(params):
    return q("""
        MATCH (caller:Function)-[:CALLS]->(callee:Function {name:$fn})
        RETURN caller.name AS caller, caller.file AS caller_file
    """, fn=params["fn"])

def unresolved(_):
    return q("""
        MATCH (f:Function:ReferenceFunction)
        RETURN f.name AS name, f.file AS first_seen_in
    """)

# Add MCP protocol handlers
def initialize(params):
    """Handle MCP initialize method."""
    logging.info(f"MCP initialize with params: {params}")

    # Define the tools we expose through MCP
    tools = [
        {
            "name": "summary",
            "description": "Get a summary of the code graph",
            "parameters": {}
        },
        {
            "name": "listFiles",
            "description": "List all files in the codebase",
            "parameters": {}
        },
        {
            "name": "listFunctions",
            "description": "List all functions in a file",
            "parameters": {
                "file": {
                    "type": "string",
                    "description": "File path"
                }
            }
        },
        {
            "name": "listClasses",
            "description": "List all classes in a file",
            "parameters": {
                "file": {
                    "type": "string",
                    "description": "File path"
                }
            }
        },
        {
            "name": "callees",
            "description": "Find functions called by a specific function",
            "parameters": {
                "fn": {
                    "type": "string",
                    "description": "Function name"
                }
            }
        },
        {
            "name": "callers",
            "description": "Find functions that call a specific function",
            "parameters": {
                "fn": {
                    "type": "string",
                    "description": "Function name"
                }
            }
        },
        {
            "name": "unresolved",
            "description": "List unresolved function references",
            "parameters": {}
        }
    ]

    return {
        "capabilities": {
            "tools": True
        },
        "tools": tools
    }

def shutdown(params):
    """Handle MCP shutdown method."""
    logging.info(f"MCP shutdown with params: {params}")
    return {}

# Handle unknown methods
def handle_unknown_method(params):
    """Generic handler for methods not explicitly defined."""
    # Just return an empty result rather than error
    logging.info(f"Received unsupported method, params: {params}")
    return {}

DISPATCH = {
    # Neo4j query methods
    "summary"        : graph_summary,
    "listFiles"      : list_files,
    "listFilePaths"  : list_filepaths,
    "listFunctions"  : list_functions,
    "listClasses"    : list_classes,
    "callees"        : callees,
    "callers"        : callers,
    "unresolved"     : unresolved,

    # MCP protocol methods
    "initialize"     : initialize,
    "shutdown"       : shutdown,
}

# ---------------------------------------------------------------------------
# FASTAPI / SSE IMPLEMENTATION
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful startup/shutdown for the Neo4j driver."""
    logging.info("Neo4j driver ready (URI=%s)", NEO4J_URI)
    yield
    # Handle both async and sync drivers
    try:
        if hasattr(driver, 'close') and callable(driver.close):
            if asyncio.iscoroutinefunction(driver.close):
                await driver.close()
            else:
                driver.close()
        logging.info("Neo4j driver closed")
    except Exception as e:
        logging.error(f"Error closing Neo4j driver: {e}")

app = FastAPI(lifespan=lifespan)

# Healthcheck
@app.get("/health", tags=["meta"])
def health():
    if driver is None:
        raise HTTPException(503, detail="Neo4j driver not initialized")

    try:
        with driver.session() as session:
            session.run("RETURN 1 AS ok")
        return {"status": "ok", "neo4j_uri": NEO4J_URI}
    except Exception as e:
        raise HTTPException(503, detail=f"Neo4j error: {str(e)}")

@app.get("/sse", tags=["mcp"])
async def sse_endpoint_get(request: Request):
    """Single endpoint that speaks MCP over Server-Sent Events (GET method)."""
    return await handle_sse_request(request)

@app.post("/sse", tags=["mcp"])
async def sse_endpoint_post(request: Request):
    """Single endpoint that speaks MCP over Server-Sent Events (POST method)."""
    return await handle_sse_request(request)

async def handle_sse_request(request: Request):
    """Common handler for both GET and POST SSE requests."""

    # Log request details to help debug
    origin = request.headers.get("origin", "NONE")
    logging.info(f"SSE request received: Method={request.method}, Origin={origin}")
    logging.info(f"All headers: {dict(request.headers)}")

    # --- Basic CORS check (optional) ---
    if ALLOWED_ORIGINS and origin not in ALLOWED_ORIGINS:
        logging.warning(f"Origin not allowed: {origin} not in {ALLOWED_ORIGINS}")
        # Temporarily comment out to troubleshoot
        # raise HTTPException(403, "Origin not allowed")

    # Allow all origins for troubleshooting
    # CORS check is temporarily disabled

    async def event_stream() -> AsyncGenerator[str, None]:
        # 1. MCP Handshake message
        handshake = {
            "jsonrpc": "2.0",
            "method": "handshake",
            "params": {
                "schema": "mcp:1",
                "name": "code_graph",
                "description": "Query Neo4j code graph (read-only)",
                "version": "1.0.0",
                "capabilities": {
                    "tools": True
                }
            }
        }
        logging.info(f"Sending handshake: {json.dumps(handshake)}")
        yield json.dumps(handshake)

        # 2. Listen for incoming JSON-RPC lines on the request body
        async for chunk in request.stream():
            line = chunk.decode().strip()
            if not line:
                continue

            logging.info(f"Received line: {line}")

            try:
                # Parse the request
                req_obj = json.loads(line)
                logging.info(f"Parsed JSON: {req_obj}")

                # Extract fields, being tolerant of different formats
                _id = req_obj.get("id")

                # Support both "method" and "jsonrpc.method" formats
                method = req_obj.get("method")
                if method is None and isinstance(req_obj.get("jsonrpc"), dict):
                    method = req_obj.get("jsonrpc", {}).get("method")

                # Support various parameter formats
                params = {}
                if "params" in req_obj and req_obj["params"]:
                    params = req_obj["params"]
                elif "arguments" in req_obj and req_obj["arguments"]:
                    params = req_obj["arguments"]

                logging.info(f"Extracted: id={_id}, method={method}, params={params}")

                if not method:
                    raise ValueError("No method specified in request")

                # Get the appropriate handler, falling back to unknown handler
                handler = DISPATCH.get(method, handle_unknown_method)

                # Execute handler
                result = handler(params)

                # Format response in JSON-RPC 2.0 format
                response = {
                    "jsonrpc": "2.0",
                    "id": _id,
                    "result": result
                }

                response_json = json.dumps(response)
                logging.info(f"Sending response: {response_json[:100]}...")
                yield response_json

            except json.JSONDecodeError as e:
                logging.exception(f"Failed to parse JSON: {line}")
                yield json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                })
            except Exception as exc:
                # Standard JSON-RPC error format
                logging.exception(f"Error processing request: {exc}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": req_obj.get("id") if "req_obj" in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(exc)}"
                    }
                }
                yield json.dumps(error_response)

    return EventSourceResponse(event_stream(), media_type="text/event-stream")

# ---------------------------------------------------------------------------
# ENTRY-POINT (for local dev)  ->  uvicorn code_graph_http:app --reload
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    uvicorn.run("code_graph_http:app",
                host=args.host, port=args.port, reload=False, log_level="info")
