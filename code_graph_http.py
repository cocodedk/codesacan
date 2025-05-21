#!/usr/bin/env python3
"""
code_graph_http.py

FastAPI + SSE server that implements Cursor’s Model Context Protocol (MCP)
for querying the Neo4j code-graph created by scanner.py.  Read-only: it never
runs the scanner—only answers Cypher queries.

Dependencies
------------
pip install fastapi uvicorn sse-starlette neo4j python-dotenv

Environment (.env)
------------------
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme
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

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
ALLOWED_ORIGINS = set(
    [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_lifetime=300,
    connection_timeout=20,
)

# ---------------------------------------------------------------------------
# CYTHER HELPERS
# ---------------------------------------------------------------------------

def q(cypher: str, **params) -> list[Dict[str, Any]]:
    """Run a Cypher query and return list of dicts."""
    with driver.session() as s:
        return [r.data() for r in s.run(cypher, **params)]

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

DISPATCH = {
    "summary"        : graph_summary,
    "listFiles"      : list_files,
    "listFilePaths"  : list_filepaths,
    "listFunctions"  : list_functions,
    "listClasses"    : list_classes,
    "callees"        : callees,
    "callers"        : callers,
    "unresolved"     : unresolved,
}

# ---------------------------------------------------------------------------
# FASTAPI / SSE IMPLEMENTATION
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Graceful startup/shutdown for the Neo4j driver."""
    logging.info("Neo4j driver ready (URI=%s)", NEO4J_URI)
    yield
    await driver.close()
    logging.info("Neo4j driver closed")

app = FastAPI(lifespan=lifespan)

# Healthcheck
@app.get("/health", tags=["meta"])
def health():
    try:
        q("RETURN 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(503, detail=str(e))

@app.get("/sse", tags=["mcp"])
async def sse_endpoint(request: Request):
    """Single endpoint that speaks MCP over Server-Sent Events."""

    # --- Basic CORS check (optional) ---
    if ALLOWED_ORIGINS and request.headers.get("origin") not in ALLOWED_ORIGINS:
        raise HTTPException(403, "Origin not allowed")

    async def event_stream() -> AsyncGenerator[str, None]:
        # 1. Handshake (must be first line)
        yield json.dumps({
            "schema": "mcp:1",
            "name":   "code_graph",
            "description": "Query Neo4j code graph (read-only)"
        })

        # 2. Listen for incoming JSON-RPC lines on the request body
        async for chunk in request.stream():
            line = chunk.decode().strip()
            if not line:
                continue
            try:
                req_obj = json.loads(line)
                _id     = req_obj.get("id")
                method  = req_obj.get("method")
                params  = req_obj.get("params", {})

                if method not in DISPATCH:
                    raise ValueError(f"unknown method {method}")

                # Execute handler (sync but fast—DB I/O hidden in Neo4j driver)
                result = DISPATCH[method](params)
                yield json.dumps({"id": _id, "result": result})

            except Exception as exc:
                # Bubble structured error
                logging.exception("Error handling request line: %s", line)
                yield json.dumps({"id": req_obj.get("id"), "error": str(exc)})

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
