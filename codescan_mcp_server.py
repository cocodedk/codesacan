#!/usr/bin/env python3
"""
codescan_mcp_server.py - MCP Server using FastMCP and stdio.
Provides tools to query a Neo4j database populated with code analysis data.
"""
import os
import logging
import subprocess
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

@mcp.tool()
def uncalled_functions() -> List[Dict[str, Any]]:
    """
    List all user-defined functions that are not called by any other function.

    Returns:
        List of functions (name, file, line, end_line) that have no incoming CALLS relationships.
    """
    return q(
        """
        MATCH (f:Function)
        WHERE coalesce(f.is_reference, false) = false
          AND NOT (():Function)-[:CALLS]->(f)
        RETURN f.name AS name, f.file AS file, f.line AS line, f.end_line AS end_line
        ORDER BY f.file, f.line
        """
    )

@mcp.tool()
def most_called_functions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List functions with the most callers (fan-in).
    Args:
        limit: Maximum number of results to return (default 10)
    Returns:
        List of functions with their name, file, and number of callers.
    """
    return q(
        """
        MATCH (f:Function)
        WHERE coalesce(f.is_reference, false) = false
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(f)
        WITH f, count(caller) AS num_callers
        ORDER BY num_callers DESC, f.file, f.line
        RETURN f.name AS name, f.file AS file, num_callers
        LIMIT $limit
        """,
        limit=limit
    )

@mcp.tool()
def most_calling_functions(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List functions that call the most other functions (fan-out).
    Args:
        limit: Maximum number of results to return (default 10)
    Returns:
        List of functions with their name, file, and number of callees.
    """
    return q(
        """
        MATCH (f:Function)
        WHERE coalesce(f.is_reference, false) = false
        OPTIONAL MATCH (f)-[:CALLS]->(callee:Function)
        WITH f, count(callee) AS num_callees
        ORDER BY num_callees DESC, f.file, f.line
        RETURN f.name AS name, f.file AS file, num_callees
        LIMIT $limit
        """,
        limit=limit
    )

@mcp.tool()
def recursive_functions() -> List[Dict[str, Any]]:
    """
    List functions that call themselves (direct recursion).
    Returns:
        List of recursive functions with their name and file.
    """
    return q(
        """
        MATCH (f:Function)-[:CALLS]->(f2:Function)
        WHERE f = f2 AND coalesce(f.is_reference, false) = false
        RETURN f.name AS name, f.file AS file, f.line AS line
        ORDER BY f.file, f.line
        """
    )

@mcp.tool()
def classes_with_no_methods() -> List[Dict[str, Any]]:
    """
    List classes that do not contain any methods.
    Returns:
        List of class names and files with no outgoing CONTAINS relationships.
    """
    return q(
        """
        MATCH (c:Class)
        WHERE NOT (c)-[:CONTAINS]->(:Function)
        RETURN c.name AS class, c.file AS file, c.line AS line
        ORDER BY c.file, c.line
        """
    )

@mcp.tool()
def functions_calling_references() -> List[Dict[str, Any]]:
    """
    List functions that call at least one reference function (potential missing dependencies).
    Returns:
        List of function names, files, and the number of reference functions they call.
    """
    return q(
        """
        MATCH (f:Function)-[:CALLS]->(ref:Function:ReferenceFunction)
        WHERE coalesce(f.is_reference, false) = false
        WITH f, count(ref) AS num_reference_calls
        RETURN f.name AS name, f.file AS file, num_reference_calls
        ORDER BY num_reference_calls DESC, f.file, f.line
        """
    )

@mcp.tool()
def classes_with_most_methods(limit: int = 10) -> List[Dict[str, Any]]:
    """
    List classes with the most methods.
    Args:
        limit: Maximum number of results to return (default 10)
    Returns:
        List of class names, files, and method counts.
    """
    return q(
        """
        MATCH (c:Class)
        OPTIONAL MATCH (c)-[:CONTAINS]->(f:Function)
        WITH c, count(f) AS num_methods
        ORDER BY num_methods DESC, c.file, c.line
        RETURN c.name AS class, c.file AS file, num_methods
        LIMIT $limit
        """,
        limit=limit
    )

@mcp.tool()
def function_call_arguments(fn: str, file: str = None) -> List[Dict[str, Any]]:
    """
    List all argument lists used in calls to a given function.
    Args:
        fn: Name of the function to inspect
        file: (Optional) File path to disambiguate overloaded or class methods
    Returns:
        List of argument lists, with caller name, caller file, and call site line number.
    """
    cypher = """
        MATCH (caller:Function)-[call:CALLS]->(callee:Function {name:$fn})
        """
    if file:
        cypher += " WHERE callee.file = $file"
    cypher += """
        RETURN DISTINCT call.args AS args, caller.name AS caller, caller.file AS caller_file, call.line AS line
        ORDER BY line
    """
    params = {"fn": fn}
    if file:
        params["file"] = file
    return q(cypher, **params)

@mcp.tool()
def rescan_codebase() -> dict:
    """
    Run scanner.py to re-analyze the codebase and repopulate the Neo4j database.
    Returns:
        A dictionary with keys: success (bool), output (str), error (str or None)
    """
    try:
        proc = subprocess.run([
            'python', 'scanner.py'
        ], capture_output=True, text=True, timeout=600)
        return {
            'success': proc.returncode == 0,
            'output': proc.stdout,
            'error': proc.stderr if proc.returncode != 0 else None
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e)
        }

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
