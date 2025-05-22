#!/bin/bash
# run_mcp_stdio_server.sh - Launch the CodeScan MCP stdio server
# Redirects all standard output to stderr to avoid interfering with JSON-RPC

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Source the virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
  # Activate and redirect activation messages to stderr
  source "$SCRIPT_DIR/venv/bin/activate" 2>/dev/null
else
  echo "Virtual environment not found at $SCRIPT_DIR/venv" >&2
  exit 1
fi

# Execute the modular MCP server
exec python "$SCRIPT_DIR/codescan_mcp_server.py"
