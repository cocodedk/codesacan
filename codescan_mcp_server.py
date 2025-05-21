#!/usr/bin/env python3
"""
codescan_mcp_server.py - MCP Server using FastMCP and stdio.
Provides tools to query a Neo4j database populated with code analysis data.
"""
import os
import logging
import subprocess
import sys
from typing import List, Dict, Any, Optional
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from neo4j import GraphDatabase, basic_auth
from mcp.server.fastmcp import FastMCP

# --- Configuration & Setup ---
load_dotenv(".env", override=True)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7600")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "strongpassword")
DEBUG_MCP = os.getenv("DEBUG_MCP", "false").lower() in ("true", "1", "yes")
LOG_FILE = os.getenv("LOG_FILE", "codescan_mcp_server.log")
MCP_SERVER_LOGGING_ENABLED = os.getenv("MCP_SERVER_LOGGING_ENABLED", "true").lower() in ("true", "1", "yes")

# --- Important: Create a proper stderr print function ---
# This ensures startup messages don't interfere with JSON-RPC protocol
def stderr_print(*args, **kwargs):
    """Print to stderr to avoid interfering with JSON-RPC protocol."""
    kwargs['file'] = sys.stderr
    kwargs['flush'] = True
    print(*args, **kwargs)

# --- Logging Setup ---
logger = logging.getLogger("codescan_mcp_server")

if MCP_SERVER_LOGGING_ENABLED:
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    log_file_path = os.path.join("logs", LOG_FILE)

    logger.setLevel(logging.DEBUG if DEBUG_MCP else logging.INFO)

    # Console handler - IMPORTANT: Use stderr instead of stdout
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if DEBUG_MCP else logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    logger.addHandler(file_handler)
    logger.info(f"Logging enabled. Level: {'DEBUG' if DEBUG_MCP else 'INFO'}. Log file: {os.path.abspath(log_file_path)}")
else:
    logger.setLevel(logging.CRITICAL + 1) # Effectively disable logging
    # Still need a basic print to stderr for this specific case, as logger is disabled.
    stderr_print("Logging is disabled via MCP_SERVER_LOGGING_ENABLED.")

# --- Neo4j Connection Verification ---
def verify_database_connection() -> Dict[str, Any]:
    """Verify connection to Neo4j database and return status."""
    connection_info = {
        "success": False,
        "uri": NEO4J_URI,
        "user": NEO4J_USER,
        "port": NEO4J_URI.split(":")[-1] if ":" in NEO4J_URI else "7687",
        "error": None
    }

    driver = None
    try:
        logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD)
        )

        # Test connection with a simple query
        with driver.session() as session:
            result = session.run("RETURN 1 AS ok").single()
            if result and result.get("ok") == 1:
                connection_info["success"] = True
                logger.info(f"Successfully connected to Neo4j at {NEO4J_URI}")
            else:
                connection_info["error"] = "Connected but query returned unexpected result"
                logger.error(connection_info["error"])

    except Exception as e:
        error_msg = f"Failed to connect to Neo4j: {str(e)}"
        connection_info["error"] = error_msg
        logger.error(error_msg)

    finally:
        if driver:
            driver.close()

    return connection_info

# --- Neo4j Driver ---
driver = None
# Store the initial connection status in a variable with a different name
initial_connection_status = verify_database_connection()
if initial_connection_status["success"]:
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD)
        )
    except Exception as e:
        logger.error(f"Failed to create Neo4j driver: {e}")

# --- Initialize FastMCP ---
mcp = FastMCP("codescan_neo4j",
              description="Neo4j code graph analyzer for Python codebases",
              version="1.0.0")

# --- Query Helper ---
def q(cypher: str, **params) -> List[Dict[str, Any]]:
    """Run a Cypher query and return list of dicts."""
    if MCP_SERVER_LOGGING_ENABLED and DEBUG_MCP:
        logger.debug(f"Executing Cypher Query: {cypher}")
        if params:
            logger.debug(f"Query Parameters: {params}")

    if driver is None:
        logger.error("Neo4j driver not available for query.")
        return []
    try:
        with driver.session() as s:
            results = [r.data() for r in s.run(cypher, **params)]
            if MCP_SERVER_LOGGING_ENABLED and DEBUG_MCP:
                logger.debug(f"Query returned {len(results)} rows.")
            return results
    except Exception as e:
        logger.error(f"Neo4j query error: {e}")
        return []

# --- Tool Definitions ---
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

@mcp.tool()
def list_test_functions() -> List[Dict[str, Any]]:
    """
    List all test functions.

    Returns:
        List of test functions with their names, files, and line numbers
    """
    return q("""
        MATCH (f:TestFunction)
        RETURN f.name AS name, f.file AS file, f.line AS line, f.end_line AS end_line
        ORDER BY f.file, f.line
    """)

@mcp.tool()
def list_example_functions() -> List[Dict[str, Any]]:
    """
    List all example functions.

    Returns:
        List of example functions with their names, files, and line numbers
    """
    return q("""
        MATCH (f:ExampleFunction)
        RETURN f.name AS name, f.file AS file, f.line AS line, f.end_line AS end_line
        ORDER BY f.file, f.line
    """)

@mcp.tool()
def list_test_classes() -> List[Dict[str, Any]]:
    """
    List all test classes.

    Returns:
        List of test classes with their names, files, and line numbers
    """
    return q("""
        MATCH (c:TestClass)
        RETURN c.name AS name, c.file AS file, c.line AS line, c.end_line AS end_line
        ORDER BY c.file, c.line
    """)

@mcp.tool()
def list_example_classes() -> List[Dict[str, Any]]:
    """
    List all example classes.

    Returns:
        List of example classes with their names, files, and line numbers
    """
    return q("""
        MATCH (c:ExampleClass)
        RETURN c.name AS name, c.file AS file, c.line AS line, c.end_line AS end_line
        ORDER BY c.file, c.line
    """)

@mcp.tool()
def get_test_files() -> List[Dict[str, str]]:
    """
    List all files containing tests.

    Returns:
        List of file paths containing test components
    """
    return q("""
        MATCH (n:Test)
        RETURN DISTINCT n.file AS file
        ORDER BY file
    """)

@mcp.tool()
def get_example_files() -> List[Dict[str, str]]:
    """
    List all files containing examples.

    Returns:
        List of file paths containing example components
    """
    return q("""
        MATCH (n:Example)
        RETURN DISTINCT n.file AS file
        ORDER BY file
    """)

@mcp.tool()
def test_detection_config() -> Dict[str, List[str]]:
    """
    Get the current test detection configuration.

    Returns:
        Dictionary with test detection pattern configuration
    """
    # Import the config from scanner
    import scanner

    return {
        "test_dir_patterns": scanner.TEST_DIR_PATTERNS,
        "test_file_patterns": scanner.TEST_FILE_PATTERNS,
        "test_function_prefixes": scanner.TEST_FUNCTION_PREFIXES,
        "test_class_patterns": scanner.TEST_CLASS_PATTERNS
    }

@mcp.tool()
def untested_functions(exclude_private: bool = True) -> List[Dict[str, Any]]:
    """
    List functions without tests.

    Args:
        exclude_private: Whether to exclude private functions (starting with _)

    Returns:
        List of functions that don't have any tests covering them
    """
    where_clause = "WHERE NOT f:TestFunction AND NOT (:TestFunction)-[:TESTS]->(f)"

    if exclude_private:
        where_clause += " AND NOT f.name STARTS WITH '_'"

    return q(f"""
        MATCH (f:Function)
        {where_clause}
        RETURN f.name AS name, f.file AS file, f.line AS line
        ORDER BY f.file, f.line
    """)

@mcp.tool()
def test_coverage_ratio() -> List[Dict[str, Any]]:
    """
    Get test coverage ratio.

    Returns:
        Overall test coverage ratio and counts
    """
    return q("""
        MATCH (f:Function) WHERE NOT f:TestFunction
        WITH count(f) AS total_functions
        MATCH (f:Function) WHERE NOT f:TestFunction
          AND (:TestFunction)-[:TESTS]->(f)
        WITH total_functions, count(f) AS tested_functions
        RETURN
            total_functions,
            tested_functions,
            CASE
                WHEN total_functions > 0 THEN toFloat(tested_functions) / total_functions
                ELSE 0
            END AS coverage_ratio
    """)

@mcp.tool()
def functions_tested_by(file: str) -> List[Dict[str, Any]]:
    """
    List functions tested by a specific test file.

    Args:
        file: Path to the test file

    Returns:
        List of functions tested by the specified test file
    """
    return q("""
        MATCH (test:TestFunction {file: $file})-[r:TESTS]->(f:Function)
        RETURN f.name AS tested_name, f.file AS tested_file, r.method AS method
        ORDER BY f.file, f.line
    """, file=file)

@mcp.tool()
def tests_for_function(name: str, file: str = None) -> List[Dict[str, Any]]:
    """
    List tests for a specific function.

    Args:
        name: Name of the function
        file: Optional file path to disambiguate functions with the same name

    Returns:
        List of test functions that test the specified function
    """
    query = """
        MATCH (test:TestFunction)-[r:TESTS]->(f:Function {name: $name})
    """
    params = {"name": name}

    if file:
        query += " WHERE f.file = $file"
        params["file"] = file

    query += """
        RETURN test.name AS test_name, test.file AS test_file, r.method AS method
        ORDER BY test.file, test.line
    """

    return q(query, **params)

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting CodeScan MCP Server (FastMCP, stdio)")
    logger.info(f"Database connection status: {'Success' if initial_connection_status['success'] else 'Failed'}")
    if not initial_connection_status['success']:
        logger.warning(f"Connection details: URI={NEO4J_URI}, USER={NEO4J_USER}, PORT={initial_connection_status['port']}")
        logger.error(f"Connection error: {initial_connection_status['error']}")

    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
    finally:
        if driver:
            driver.close()
            logger.info("Neo4j driver closed")
