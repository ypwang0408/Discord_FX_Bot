#!/bin/bash

# Discord Bot Stop Script (Modular Version)

SESSION_NAME="discord-bot"

# Resolve script/project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load .env from project root if present (allows overriding BOT_DIR)
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck disable=SC1090
    source "$PROJECT_ROOT/.env"
fi

# Default BOT_DIR to project root if not set in .env
: "${BOT_DIR:=$PROJECT_ROOT}"

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
if pgrep -f "$BOT_DIR/main.py" > /dev/null; then
    echo "⚠️  Process still running, attempting to kill..."
    pkill -f "$BOT_DIR/main.py"
    sleep 2
    if pgrep -f "$BOT_DIR/main.py" > /dev/null; then
        echo "❌ Failed to stop process, you may need to kill it manually:"
        echo "   kill $(pgrep -f $BOT_DIR/main.py)"
    else
        echo "✅ Process successfully stopped"
    fi
else
    echo "✅ All processes stopped successfully"
fi
