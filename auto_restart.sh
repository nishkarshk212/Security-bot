#!/bin/bash
# Bot Auto-Restart Script with Crash Recovery
# This script monitors the bot and automatically restarts it if it crashes

BOT_SCRIPT="bot.py"
LOG_FILE="bot_monitor.log"
MAX_RESTARTS=10
RESTART_WINDOW=300  # 5 minutes in seconds
VIRTUAL_ENV=".venv/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if bot is running
is_bot_running() {
    pgrep -f "python.*$BOT_SCRIPT" > /dev/null 2>&1
    return $?
}

# Function to stop the bot
stop_bot() {
    log_message "${YELLOW}Stopping bot...${NC}"
    pkill -f "python.*$BOT_SCRIPT"
    sleep 2
    
    # Force kill if still running
    if is_bot_running; then
        log_message "${RED}Force killing bot...${NC}"
        pkill -9 -f "python.*$BOT_SCRIPT"
        sleep 1
    fi
    
    log_message "${GREEN}Bot stopped${NC}"
}

# Function to start the bot
start_bot() {
    log_message "${GREEN}Starting bot...${NC}"
    
    # Check if virtual environment exists
    if [ ! -f "$VIRTUAL_ENV" ]; then
        log_message "${RED}Virtual environment not found! Creating...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Start bot in background
    nohup .venv/bin/python "$BOT_SCRIPT" > bot_output.log 2>&1 &
    BOT_PID=$!
    
    log_message "${GREEN}Bot started with PID: $BOT_PID${NC}"
    echo $BOT_PID > bot.pid
    
    # Wait a bit to check if it stays running
    sleep 3
    
    if is_bot_running; then
        log_message "${GREEN}Bot is running successfully${NC}"
        return 0
    else
        log_message "${RED}Bot failed to start${NC}"
        return 1
    fi
}

# Function to restart the bot
restart_bot() {
    log_message "${YELLOW}Restarting bot...${NC}"
    stop_bot
    sleep 2
    start_bot
}

# Track restart times for crash detection
declare -a RESTART_TIMES

# Function to check for rapid crashes
check_rapid_crashes() {
    current_time=$(date +%s)
    
    # Add current restart time
    RESTART_TIMES+=($current_time)
    
    # Remove old entries outside the window
    local new_times=()
    for time in "${RESTART_TIMES[@]}"; do
        if (( current_time - time < RESTART_WINDOW )); then
            new_times+=($time)
        fi
    done
    RESTART_TIMES=("${new_times[@]}")
    
    # Check if we exceeded max restarts
    if [ ${#RESTART_TIMES[@]} -ge $MAX_RESTARTS ]; then
        log_message "${RED}⚠️  Bot crashed ${MAX_RESTARTS} times in ${RESTART_WINDOW} seconds!${NC}"
        log_message "${RED}Possible infinite crash loop. Waiting 60 seconds before next restart...${NC}"
        sleep 60
        
        # Clear restart times after waiting
        RESTART_TIMES=()
    fi
}

# Main monitoring loop
monitor_bot() {
    log_message "${GREEN}=========================================${NC}"
    log_message "${GREEN}Bot Monitor Started${NC}"
    log_message "${GREEN}Monitoring: $BOT_SCRIPT${NC}"
    log_message "${GREEN}=========================================${NC}"
    
    while true; do
        if ! is_bot_running; then
            log_message "${RED}⚠️  Bot is not running!${NC}"
            check_rapid_crashes
            start_bot
        fi
        
        # Check every 5 seconds
        sleep 5
    done
}

# Handle script arguments
case "$1" in
    start)
        if is_bot_running; then
            log_message "${YELLOW}Bot is already running${NC}"
        else
            start_bot
            monitor_bot &
        fi
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        if is_bot_running; then
            PID=$(pgrep -f "python.*$BOT_SCRIPT")
            log_message "${GREEN}Bot is running (PID: $PID)${NC}"
        else
            log_message "${RED}Bot is not running${NC}"
        fi
        ;;
    monitor)
        monitor_bot
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor}"
        echo ""
        echo "Commands:"
        echo "  start   - Start bot and begin monitoring"
        echo "  stop    - Stop the bot"
        echo "  restart - Restart the bot"
        echo "  status  - Check if bot is running"
        echo "  monitor - Start monitoring only (assumes bot is already running)"
        exit 1
        ;;
esac

exit 0
