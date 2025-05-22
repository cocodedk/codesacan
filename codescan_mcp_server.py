#!/usr/bin/env python3
"""
codescan_mcp_server.py - MCP Server using FastMCP and stdio.
Provides tools to query a Neo4j database populated with code analysis data.
"""
import sys
from codescan_lib.mcp_tools.base import (
    logger, mcp, driver, verify_database_connection, initial_connection_status
)

# Import all tools
from codescan_lib.mcp_tools.core import *
from codescan_lib.mcp_tools.file_tools import *
from codescan_lib.mcp_tools.call_graph import *
from codescan_lib.mcp_tools.class_tools import *
from codescan_lib.mcp_tools.constant_tools import *
from codescan_lib.mcp_tools.test_tools import *

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting CodeScan MCP Server (FastMCP, stdio)")
    logger.info(f"Database connection status: {'Success' if initial_connection_status['success'] else 'Failed'}")
    if not initial_connection_status['success']:
        logger.warning(f"Connection details: URI={initial_connection_status['uri']}, USER={initial_connection_status['user']}, PORT={initial_connection_status['port']}")
        logger.error(f"Connection error: {initial_connection_status['error']}")

    try:
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
    finally:
        if driver:
            driver.close()
            logger.info("Neo4j driver closed")
