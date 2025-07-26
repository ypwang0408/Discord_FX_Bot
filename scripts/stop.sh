#!/bin/bash

# Discord Bot Stop Script (Modular Version)

SESSION_NAME="discord-bot"

echo "🛑 Stopping E.SUN Bank JPY Exchange Rate Monitor Discord Bot (Modular Version)..."

# Check if session exists
if ! tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "❌ tmux session '$SESSION_NAME' not found"
    echo "📋 Available sessions:"
    tmux list-sessions 2>/dev/null || echo "   (None)"
    exit 1
fi

# Kill tmux session
tmux kill-session -t $SESSION_NAME

echo "✅ Bot session '$SESSION_NAME' stopped"

# Double check if process is still running
if pgrep -f "main.py" > /dev/null; then
    echo "⚠️  Process still running, attempting to kill..."
    pkill -f "main.py"
    sleep 2
    if pgrep -f "main.py" > /dev/null; then
        echo "❌ Failed to stop process, you may need to kill it manually:"
        echo "   kill $(pgrep -f main.py)"
    else
        echo "✅ Process successfully stopped"
    fi
else
    echo "✅ All processes stopped successfully"
fi
