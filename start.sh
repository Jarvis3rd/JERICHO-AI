#!/bin/bash
# start.sh — runs both the LiveKit agent worker and the Flask token server
# in a single Railway service (fallback if you don't want two services).
#
# Preferred: use two separate Railway services (see README_RAILWAY.md).
# This script is a quick-start alternative for hobby/dev deployments.

set -e

echo "Starting Jericho agent worker..."
python agent.py start &
AGENT_PID=$!

echo "Starting token server..."
python token_server.py &
SERVER_PID=$!

# If either process exits, kill the other and exit
wait -n $AGENT_PID $SERVER_PID
EXIT_CODE=$?

echo "A process exited (code $EXIT_CODE) — shutting down both..."
kill $AGENT_PID $SERVER_PID 2>/dev/null
exit $EXIT_CODE
