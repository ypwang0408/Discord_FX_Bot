#!/bin/bash

# Discord Bot Status Check Script (Modular Version)

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

echo "📊 Checking Discord Bot status (Modular Version)..."

# Check if tmux session exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "✅ Bot session '$SESSION_NAME' is running"
    
    # Show session info
    echo ""
    echo "📋 Session info:"
    tmux list-sessions | grep $SESSION_NAME
    
    echo ""
    echo "💡 Management commands:"
    echo "   View Bot logs:      tmux attach -t $SESSION_NAME"
    echo "   Stop Bot:           $BOT_DIR/scripts/stop.sh"
    echo "   Restart Bot:        $BOT_DIR/bot.sh restart"
    
    echo ""
    echo "🔍 Bot process info:"
    if pgrep -f "$BOT_DIR/main.py" > /dev/null; then
        echo "   ✅ main.py process is running"
        echo "   PID: $(pgrep -f $BOT_DIR/main.py)"
    else
        echo "   ⚠️  main.py process not found"
    fi
    
else
    echo "❌ Bot session '$SESSION_NAME' is not running"
    
    echo ""
    echo "🚀 Start Bot:"
    echo "   $BOT_DIR/scripts/start.sh"
    
    # Check if there are other sessions
    if tmux list-sessions 2>/dev/null | grep -q .; then
        echo ""
        echo "📋 Other available sessions:"
        tmux list-sessions 2>/dev/null
    fi
fi
