"""
Core MCP tools.

This module contains core tools for the MCP server, such as
connection status and graph summary.
"""
from typing import Dict, Any, List

from .base import mcp, verify_database_connection, q

@mcp.tool(name="connection_status")
def get_connection_status_tool() -> Dict[str, Any]:
    """
    Get the status of the Neo4j database connection.
    Returns connection details and success status.
    """
    return verify_database_connection()

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
def rescan_codebase() -> dict:
    """
    Run scanner.py to re-analyze the codebase and repopulate the Neo4j database.
    Returns:
        A dictionary with keys: success (bool), output (str), error (str or None)
    """
    import subprocess
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
