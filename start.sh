#!/bin/bash

echo "Starting MCP Server on port 8080..."
node cli.js --headless --browser chromium --port 8080 --host localhost --allowed-hosts '*' &
MCP_PID=$!

echo "Waiting for MCP server to start..."
sleep 5

echo "Starting App Server on port 5000..."
node app/server.js

echo "Shutting down..."
kill $MCP_PID 2>/dev/null
