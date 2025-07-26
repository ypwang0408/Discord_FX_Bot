#!/bin/bash

# Discord Bot Management Script (Modular Version)
# Simple wrapper for common bot operations

case "$1" in
    start)
        echo "🚀 Starting Discord Bot..."
        ./scripts/start.sh
        ;;
    stop)
        echo "🛑 Stopping Discord Bot..."
        ./scripts/stop.sh
        ;;
    restart)
        echo "🔄 Restarting Discord Bot..."
        ./scripts/stop.sh
        sleep 2
        ./scripts/start.sh
        ;;
    status)
        ./scripts/status.sh
        ;;
    logs)
        echo "📋 Viewing Bot logs (Press Ctrl+B then D to detach)..."
        tmux attach -t discord-bot
        ;;
    test)
        echo "🧪 Testing modular architecture..."
        source venv/bin/activate
        python -c "
from features import *
print('✅ All modules imported successfully')
print('📊 Available modules:')
print('  - ServerDataManager')
print('  - ExchangeRateMonitor') 
print('  - DataBackupManager')
print('  - RateChartGenerator')
print('  - NotificationSystem')
"
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
        echo "  $0 start     # Start the bot"
        echo "  $0 status    # Check if bot is running"
        echo "  $0 logs      # View live logs"
        exit 1
        ;;
esac
