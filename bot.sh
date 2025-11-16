#!/bin/bash

# Discord Bot Management Script (Modular Version)
# Simple wrapper for common bot operations

# Resolve project root (this script is in project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Load .env if present (allows overriding BOT_DIR)
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck disable=SC1090
    source "$PROJECT_ROOT/.env"
fi

# Default BOT_DIR to project root if not provided in .env
: "${BOT_DIR:=$PROJECT_ROOT}"

case "$1" in
    start)
        echo "🚀 Starting Discord Bot..."
        "$BOT_DIR/scripts/start.sh"
        ;;
    stop)
        echo "🛑 Stopping Discord Bot..."
        "$BOT_DIR/scripts/stop.sh"
        ;;
    restart)
        echo "🔄 Restarting Discord Bot..."
        "$BOT_DIR/scripts/stop.sh"
        sleep 2
        "$BOT_DIR/scripts/start.sh"
        ;;
    status)
        "$BOT_DIR/scripts/status.sh"
        ;;
    logs)
        echo "📋 Viewing Bot logs (Press Ctrl+B then D to detach)..."
        tmux attach -t discord-bot
        ;;
    test)
        echo "🧪 Testing modular architecture..."
        # Use venv under BOT_DIR if present
        if [ -f "$BOT_DIR/venv/bin/activate" ]; then
            # shellcheck disable=SC1090
            source "$BOT_DIR/venv/bin/activate"
        fi
        cd "$BOT_DIR"
        python3 -c "from features import *; print('✅ All modules imported successfully'); print('📊 Available modules:'); print('  - ServerDataManager'); print('  - ExchangeRateMonitor'); print('  - DataBackupManager'); print('  - RateChartGenerator'); print('  - NotificationSystem')"
        ;;
    *)
        echo "🤖 Discord Bot Management (Modular Version)"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the bot"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  status   - Check bot status"
        echo "  logs     - View bot logs (tmux session)"
        echo "  test     - Test modular architecture"
        echo ""
        echo "Examples:"
        echo "  $BOT_DIR/bot.sh start     # Start the bot"
        echo "  $BOT_DIR/bot.sh status    # Check if bot is running"
        echo "  $BOT_DIR/bot.sh logs      # View live logs"
        exit 1
        ;;
esac
