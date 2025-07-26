#!/bin/bash

# Discord Bot Startup Script (Modular Version using tmux)

SESSION_NAME="discord-bot"
BOT_DIR="/home/ypwang/discord"

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
if [ ! -f ".env" ]; then
    echo "❌ .env file not found, please create and set DISCORD_BOT_TOKEN"
    exit 1
fi

# Check Python script and modules
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

if [ ! -d "features" ]; then
    echo "❌ features directory not found"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found at ./venv"
    echo "💡 Please create virtual environment first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Create new tmux session and run in background
echo "🚀 Creating tmux session: $SESSION_NAME"

tmux new-session -d -s $SESSION_NAME -c $BOT_DIR

# Activate virtual environment and run bot in tmux session
tmux send-keys -t $SESSION_NAME "source venv/bin/activate" Enter
tmux send-keys -t $SESSION_NAME "echo '🎯 Virtual environment activated'" Enter
tmux send-keys -t $SESSION_NAME "echo '🚀 Starting modular Discord bot...'" Enter
tmux send-keys -t $SESSION_NAME "python main.py" Enter

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
