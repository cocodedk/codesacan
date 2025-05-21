#!/bin/bash
# run_mcp_stdio_server.sh - Launch the CodeScan MCP stdio server
# Redirects all standard output to stderr to avoid interfering with JSON-RPC

# Source the virtual environment
if [ -d "venv" ]; then
  # Redirect activation messages to stderr
  source venv/bin/activate 2>/dev/null
else
  echo "Virtual environment not found at ./venv" >&2
  exit 1
fi

# Run the MCP server - all stdout will be used for JSON-RPC protocol
# Any debug/info messages should go to stderr
exec python codescan_mcp_server.py
