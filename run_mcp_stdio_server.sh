#!/bin/bash
# Script to run the CodeScan MCP stdio server

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

echo "Starting CodeScan MCP Server (stdio)..."
# Execute the server script
python3 "${SCRIPT_DIR}/codescan_mcp_server.py"
