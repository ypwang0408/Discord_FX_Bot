#!/bin/bash

# Discord Bot Startup Script (Modular Version using tmux)

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

echo "🤖 Starting E.SUN Bank JPY Exchange Rate Monitor Discord Bot (Modular Version)..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not installed, please install tmux first:"
    echo "   sudo apt install tmux  # Ubuntu/Debian"
    echo "   brew install tmux      # macOS"
    exit 1
fi

# Function to handle existing session
handle_existing_session() {
    echo ""
    echo "⚠️  tmux session '$SESSION_NAME' already exists"
    echo ""
    echo "Available options:"
    echo "  1) Attach to existing session"
    echo "  2) Kill existing session and start new one"
    echo "  3) List all sessions"
    echo "  4) Exit"
    echo ""
    
    while true; do
        read -p "Please select an option (1-4): " choice
        case $choice in
            1)
                echo "🔗 Attaching to existing session..."
                tmux attach -t $SESSION_NAME
                exit 0
                ;;
            2)
                echo "🛑 Killing existing session..."
                tmux kill-session -t $SESSION_NAME
                echo "✅ Existing session killed"
                break
                ;;
            3)
                echo ""
                echo "📋 Available sessions:"
                tmux list-sessions 2>/dev/null || echo "   (None)"
                echo ""
                # Continue the loop, don't break
                ;;
            4)
                echo "👋 Exiting..."
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please enter 1, 2, 3, or 4."
                ;;
        esac
    done
}

# Check if session already exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    handle_existing_session
fi

# Change to Bot directory
cd "$BOT_DIR" || {
    echo "❌ Cannot enter directory: $BOT_DIR"
    exit 1
}

# Check environment variables file
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "❌ .env file not found in $BOT_DIR, please create and set DISCORD_BOT_TOKEN"
    exit 1
fi

# Check Python script and modules
if [ ! -f "$BOT_DIR/main.py" ]; then
    echo "❌ main.py not found in $BOT_DIR"
    exit 1
fi

if [ ! -d "$BOT_DIR/features" ]; then
    echo "❌ features directory not found in $BOT_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$BOT_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $BOT_DIR/venv"
    echo "💡 Please create virtual environment first:"
    echo "   python3 -m venv $BOT_DIR/venv"
    echo "   source $BOT_DIR/venv/bin/activate"
    echo "   pip install -r $BOT_DIR/requirements.txt"
    exit 1
fi

# Create new tmux session and run in background
echo "🚀 Creating tmux session: $SESSION_NAME"

tmux new-session -d -s $SESSION_NAME -c $BOT_DIR

# Activate virtual environment and run bot in tmux session
tmux send-keys -t $SESSION_NAME "source $BOT_DIR/venv/bin/activate" Enter
tmux send-keys -t $SESSION_NAME "echo '🎯 Virtual environment activated'" Enter
tmux send-keys -t $SESSION_NAME "echo '🚀 Starting modular Discord bot...'" Enter
tmux send-keys -t $SESSION_NAME "python3 $BOT_DIR/main.py" Enter

echo "✅ Bot started in tmux session '$SESSION_NAME'"
echo ""
echo "📋 Common commands:"
echo "   Attach to session:    tmux attach -t $SESSION_NAME"
echo "   Detach from session:  Ctrl+B, then D"
echo "   Kill session:         tmux kill-session -t $SESSION_NAME"
echo "   List sessions:        tmux list-sessions"
echo ""
echo "🔍 To check Bot status, use:"
echo "   tmux attach -t $SESSION_NAME"
