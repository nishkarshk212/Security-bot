# Quick Start - Maintenance System

## ✅ What's Been Added

### 1. **Auto-Restart System**
- Bot automatically restarts if it crashes
- Monitors bot every 5 seconds
- Prevents infinite crash loops
- Logs all restarts

### 2. **Global Ban System (Owner Only)**
- `/gban` - Globally ban a user (reply to message)
- `/ungban` - Remove global ban (reply to message)
- `/gbanlist` - Show all banned users
- Bans work across ALL groups where bot is present

### 3. **Owner Commands**
- `/restart` - Manually restart bot
- `/status` - Check bot status, uptime, restart count
- All commands restricted to OWNER_ID only

### 4. **Logging & Notifications**
- Logs sent to channel: `-1003757375746`
- Owner ID: `8791884726`
- Crash notifications
- Restart notifications
- Global ban notifications

## 🚀 How to Use

### Start Bot with Auto-Restart (Recommended)
```bash
./auto_restart.sh start
```

### Other Commands
```bash
# Check if bot is running
./auto_restart.sh status

# Stop bot
./auto_restart.sh stop

# Restart bot
./auto_restart.sh restart
```

### Owner Commands (in Telegram)
```
/gban - Reply to user's message to ban them everywhere
/ungban - Reply to user's message to unban them
/gbanlist - See all globally banned users
/restart - Restart the bot
/status - Check bot status
```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `maintenance.py` | Core maintenance logic |
| `auto_restart.sh` | Auto-restart monitoring script |
| `.env` | Updated with OWNER_ID and LOG_CHANNEL_ID |
| `MAINTENANCE.md` | Full documentation |
| `QUICK_START_MAINTENANCE.md` | This file |

## 🔧 Configuration

Already configured in `.env`:
```env
OWNER_ID=8791884726
LOG_CHANNEL_ID=-1003757375746
```

## ✨ Features Working

✅ Auto-restart on crash  
✅ Global ban system  
✅ Owner-only commands  
✅ Log channel notifications  
✅ Crash detection and recovery  
✅ Restart count tracking  
✅ Uptime monitoring  
✅ Persistent global bans  

## 🎯 Test It

1. **Test auto-restart**: Kill the bot process, it will restart automatically
2. **Test global ban**: Use `/gban` on a test user
3. **Check logs**: Look at `bot_maintenance.log` and your log channel
4. **Check status**: Use `/status` command

The bot is now running with full maintenance support! 🎉
