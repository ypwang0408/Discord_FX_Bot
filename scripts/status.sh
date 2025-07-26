#!/bin/bash

# Discord Bot Status Check Script (Modular Version)

SESSION_NAME="discord-bot"

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
    echo "   Stop Bot:           ./scripts/stop.sh"
    echo "   Restart Bot:        ./bot.sh restart"
    
    echo ""
    echo "🔍 Bot process info:"
    if pgrep -f "main.py" > /dev/null; then
        echo "   ✅ main.py process is running"
        echo "   PID: $(pgrep -f main.py)"
    else
        echo "   ⚠️  main.py process not found"
    fi
    
else
    echo "❌ Bot session '$SESSION_NAME' is not running"
    
    echo ""
    echo "🚀 Start Bot:"
    echo "   ./start.sh"
    
    # Check if there are other sessions
    if tmux list-sessions 2>/dev/null | grep -q .; then
        echo ""
        echo "📋 Other available sessions:"
        tmux list-sessions 2>/dev/null
    fi
fi
