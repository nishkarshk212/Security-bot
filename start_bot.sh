#!/bin/bash

echo "🤖 Starting Telegram Moderation Bot..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Check if requirements are installed
python3 -c "import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "✅ All checks passed!"
echo "🚀 Bot is starting..."
echo ""
echo "Bot Commands:"
echo "  /start    - Initialize the bot"
echo "  /settings - Open settings panel (admins only)"
echo "  /help     - Show help information"
echo ""
echo "Press Ctrl+C to stop the bot"
echo "================================"
echo ""

python3 bot.py
