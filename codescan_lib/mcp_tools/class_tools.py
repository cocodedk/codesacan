"""
Class-related MCP tools.

This module contains tools for working with classes.
"""
from typing import Dict, Any, List

from .base import mcp, q

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
