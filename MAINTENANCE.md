# Bot Maintenance & Auto-Restart System

## Overview

This bot includes a comprehensive maintenance system with:
- ✅ Auto-restart on crash
- ✅ Global ban system (owner only)
- ✅ Crash logging and notifications
- ✅ Manual restart command
- ✅ Bot status monitoring

## Configuration

### Environment Variables (.env)

```env
BOT_TOKEN=your_bot_token_here
OWNER_ID=8791884726
LOG_CHANNEL_ID=-1003757375746
```

- **OWNER_ID**: Telegram user ID of the bot owner
- **LOG_CHANNEL_ID**: Channel ID where logs and notifications are sent

## Features

### 1. Auto-Restart System

The bot automatically restarts if it crashes:

**Method 1: Using auto_restart.sh (Recommended)**
```bash
# Start bot with monitoring
./auto_restart.sh start

# Check status
./auto_restart.sh status

# Stop bot
./auto_restart.sh stop

# Restart bot
./auto_restart.sh restart
```

**Method 2: Built-in restart**
The bot has built-in crash detection and will attempt to restart itself automatically.

### 2. Global Ban System (Owner Only)

Commands available only to the bot owner:

#### `/gban` - Global Ban
Reply to a user's message with `/gban` to ban them from using the bot everywhere.

```
Reply to user → /gban
```

#### `/ungban` - Remove Global Ban
Reply to a user's message with `/ungban` to remove their global ban.

```
Reply to user → /ungban
```

#### `/gbanlist` - Show Global Bans
Shows all currently globally banned users.

```
/gbanlist
```

#### `/restart` - Manual Restart
Manually restart the bot.

```
/restart
```

#### `/status` - Bot Status
Shows bot uptime, restart count, and other stats.

```
/status
```

### 3. Logging

All events are logged to:
- **bot.log**: General bot logs
- **bot_maintenance.log**: Maintenance-specific logs
- **global_bans.txt**: List of globally banned user IDs
- **Log Channel**: Notifications sent to LOG_CHANNEL_ID

### 4. Crash Recovery

When the bot crashes:
1. Error is logged to files
2. Notification sent to owner and log channel
3. Bot automatically restarts
4. If crashes happen too frequently (>10 times in 5 minutes), waits 60 seconds before restarting

## Files Created

| File | Purpose |
|------|---------|
| `maintenance.py` | Maintenance module with all logic |
| `auto_restart.sh` | Shell script for monitoring and auto-restart |
| `bot.log` | General bot logs |
| `bot_maintenance.log` | Maintenance logs |
| `bot_monitor.log` | Auto-restart monitor logs |
| `global_bans.txt` | Globally banned user IDs |
| `bot.pid` | Current bot process ID |

## Usage Examples

### Starting the Bot

**Option 1: With auto-restart monitoring (Recommended)**
```bash
./auto_restart.sh start
```

**Option 2: Normal start (no auto-restart)**
```bash
python bot.py
```

### Managing Global Bans

```bash
# Ban a user
Reply to their message → /gban

# Unban a user
Reply to their message → /ungban

# View all bans
/gbanlist
```

### Checking Bot Status

```bash
# Via command
/status

# Via shell script
./auto_restart.sh status

# Check logs
tail -f bot.log
tail -f bot_maintenance.log
```

### Restarting the Bot

```bash
# Via command (owner only)
/restart

# Via shell script
./auto_restart.sh restart
```

## Log Channel Notifications

The bot sends notifications to the log channel for:
- ✅ Bot startup/restart
- ⚠️ Crash detection
- 🚫 Global ban added/removed
- 📊 Status updates

## Troubleshooting

### Bot won't start
```bash
# Check if already running
./auto_restart.sh status

# Check logs
cat bot.log
cat bot_monitor.log

# Force restart
./auto_restart.sh restart
```

### Too many restarts
If the bot crashes more than 10 times in 5 minutes, it will wait 60 seconds before restarting to prevent infinite loops.

### Clear global bans
```bash
# Edit the file directly
nano global_bans.txt

# Or use commands
/ungban (reply to each user)
```

## Security Notes

- Only the OWNER_ID can use maintenance commands
- Global bans are persistent across restarts
- All maintenance actions are logged
- Log channel should be private for security
