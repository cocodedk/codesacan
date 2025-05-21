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
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "demodemo")
DEBUG_MCP = os.getenv("DEBUG_MCP", "false").lower() in ("true", "1", "yes")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MCP else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("codescan_mcp_server")

# --- Neo4j Driver ---
driver = None
try:
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD)
    )
    with driver.session() as session:
        session.run("RETURN 1 AS ok")
    logger.info(f"Connected to Neo4j at {NEO4J_URI}")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")

# --- Initialize FastMCP ---
mcp = FastMCP("codescan_neo4j",
              description="Neo4j code graph analyzer for Python codebases")

# --- Query Helper ---
def q(cypher: str, **params) -> List[Dict[str, Any]]:
    """Run a Cypher query and return list of dicts."""
    if driver is None:
        logger.error("Neo4j driver not available for query.")
        return []
    try:
        with driver.session() as s:
            return [r.data() for r in s.run(cypher, **params)]
    except Exception as e:
        logger.error(f"Neo4j query error: {e}")
        return []

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

@mcp.tool()
def list_files() -> List[Dict[str, str]]:
    """
    List all unique file paths present in the code graph.
    """
    return q("MATCH (n) WHERE exists(n.file) RETURN DISTINCT n.file AS file ORDER BY file")

@mcp.tool()
def list_functions(file: str) -> List[Dict[str, Any]]:
    """
    List all functions defined in a specific file.

    Args:
        file: Path to the file to list functions from

    Returns:
        List of functions with their names and line numbers
    """
    return q("""
        MATCH (f:Function {file:$file})
        WHERE coalesce(f.is_reference,false)=false
        RETURN f.name AS name, f.line AS line, f.end_line AS end_line
        ORDER BY f.line
    """, file=file)

@mcp.tool()
def list_classes(file: str) -> List[Dict[str, Any]]:
    """
    List all classes defined in a specific file.

    Args:
        file: Path to the file to list classes from

    Returns:
        List of classes with their names and line numbers
    """
    return q("""
        MATCH (c:Class {file:$file})
        RETURN c.name AS class, c.line AS line, c.end_line AS end_line
        ORDER BY c.line
    """, file=file)

@mcp.tool()
def callees(fn: str) -> List[Dict[str, Any]]:
    """
    Find functions called by a specific function.

    Args:
        fn: Name of the function to find callees for

    Returns:
        List of functions called by the specified function
    """
    return q("""
        MATCH (caller:Function {name:$fn})-[:CALLS]->(callee:Function)
        RETURN callee.name AS callee, caller.file AS caller_file
    """, fn=fn)

@mcp.tool()
def callers(fn: str) -> List[Dict[str, Any]]:
    """
    Find functions that call a specific function.

    Args:
        fn: Name of the function called by others

    Returns:
        List of functions that call the specified function
    """
    return q("""
        MATCH (caller:Function)-[:CALLS]->(callee:Function {name:$fn})
        RETURN caller.name AS caller, caller.file AS caller_file
    """, fn=fn)

@mcp.tool()
def unresolved_references() -> List[Dict[str, Any]]:
    """
    List unresolved function references in the codebase.

    Returns:
        List of unresolved function references and where they were first seen
    """
    return q("""
        MATCH (f:Function:ReferenceFunction)
        RETURN f.name AS name, f.file AS first_seen_in
    """)

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
            logger.info("Neo4j driver closed")
