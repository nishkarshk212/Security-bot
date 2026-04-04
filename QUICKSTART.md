# 🚀 Quick Start Guide

## Setup (2 minutes)

### 1. Verify Installation
```bash
cd /Users/nishkarshkr/Desktop/security
ls -la
```

You should see:
- ✅ `.env` - Bot token configured
- ✅ `bot.py` - Main bot file
- ✅ `requirements.txt` - Dependencies
- ✅ `start_bot.sh` - Launch script

### 2. Start the Bot

**Option A: Using start script (Recommended)**
```bash
./start_bot.sh
```

**Option B: Direct Python**
```bash
python bot.py
```

### 3. Add Bot to Your Telegram Group

1. Search for your bot on Telegram (use @BotFather to find it)
2. Add the bot to your group
3. **Important:** Make the bot an admin with "Delete Messages" permission

### 4. Configure Settings

In your Telegram group:

```
/settings
```

This opens the interactive settings panel where you can:
- ✅ Toggle features on/off
- ⚙️ Adjust flood protection
- 🔄 Refresh settings view

---

## 📱 Bot Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/start` | Welcome message & features | Everyone |
| `/settings` | Open settings panel | Admins only |
| `/help` | Show help information | Everyone |

---

## 🎛️ Features Overview

All features can be toggled independently:

- 🚫 **Block Stickers** - Delete sticker messages
- 📸 **Block Media** - Block photos, videos, files
- ↗️ **Block Forwards** - Prevent forwarded messages
- 🔗 **Block Links** - Block URLs and links
- 🛡️ **Spam Protection** - Block duplicate messages
- 🌊 **Flood Protection** - Limit message rate

---

## ⚙️ Common Configurations

### Strict Moderation
Enable all features + Flood: 3 msgs/5s

### Moderate Moderation
Enable: Links, Forwards, Spam + Flood: 5 msgs/10s

### Light Moderation
Enable: Spam + Flood: 7 msgs/15s

---

## 🔧 Troubleshooting

**Bot not responding?**
```bash
# Check if bot is running
ps aux | grep bot.py

# Restart bot
./start_bot.sh
```

**Messages not being deleted?**
- Ensure bot is admin in the group
- Check that feature is enabled in `/settings`

**Need to change bot token?**
Edit `.env` file:
```
BOT_TOKEN=your_new_token_here
```

---

## 📚 More Information

- **Detailed Features:** See `FEATURES.md`
- **Full Documentation:** See `README.md`
- **Code Comments:** Check `bot.py` for inline documentation

---

## 🆘 Need Help?

1. Check if bot is running: `ps aux | grep bot.py`
2. View logs: Check terminal output
3. Verify settings: Use `/settings` in Telegram
4. Test with a simple message in the group

---

**That's it! Your bot is ready to moderate!** 🎉
