# Advanced Telegram Moderation Bot 🤖

A powerful Telegram bot with comprehensive group moderation features including sticker blocking, media blocking, forward message blocking, link blocking, spam protection, and flood protection with an intuitive settings panel.

## Features ✨

- **🚫 Sticker Blocking** - Automatically delete sticker messages
- **📸 Media Blocking** - Block photos, videos, documents, audio, voice messages
- **↗️ Forward Message Blocking** - Prevent forwarded messages from other chats
- **�� Link Blocking** - Block messages containing URLs (Telegram links, external links)
- **🛡️ Spam Protection** - Detect and block duplicate messages sent repeatedly
- **🌊 Flood Protection** - Limit messages per user in a time window (customizable)
- **⚙️ Beautiful Settings Panel** - Easy-to-use inline keyboard interface
- **👥 Admin Controls** - Only admins can modify settings
- **💾 Persistent Settings** - All settings saved in SQLite database

## Installation 📦

1. **Clone or download the project files**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the bot token:**
   - The `.env` file is already configured with your bot token
   - If you need to change it, edit the `BOT_TOKEN` in `.env`

## Usage 🚀

### Start the Bot

```bash
python bot.py
```

### Bot Commands

- `/start` - Initialize the bot and see welcome message
- `/settings` - Open the interactive settings panel (admins only)
- `/help` - Display help information about all features

### Setting Up in Your Group

1. Add the bot to your Telegram group
2. Make the bot an admin (required for deleting messages)
3. Use `/settings` to configure moderation options
4. The bot will automatically start moderating based on your settings

## Settings Panel 🎛️

The settings panel provides an intuitive inline keyboard interface where you can:

- Toggle each feature on/off with a single tap
- See current status of all features (✅ Enabled / ❌ Disabled)
- Adjust flood protection parameters
- Refresh settings view
- Close the panel when done

### Flood Protection Options

Choose from preset configurations:
- 3 messages / 5 seconds
- 5 messages / 10 seconds (default)
- 7 messages / 15 seconds
- 10 messages / 20 seconds

## How It Works 🔧

### Database
The bot uses SQLite (`bot_database.db`) to store:
- Group-specific settings
- User message timestamps (for flood detection)
- Message cache (for spam detection)

### Moderation Logic
1. When a message is received, the bot checks group settings
2. Admin messages bypass all restrictions
3. Each feature is checked sequentially
4. Violations result in message deletion + warning
5. Warnings auto-delete after a few seconds

### Permissions
- Only group admins can access `/settings`
- Bot needs admin privileges to delete messages
- Regular users are subject to all active restrictions

## File Structure 📁

```
security/
├── .env                 # Environment variables (bot token)
├── requirements.txt     # Python dependencies
├── bot.py              # Main bot application
├── bot_database.db     # SQLite database (created automatically)
└── README.md           # This file
```

## Configuration ⚙️

### Environment Variables (.env)

```
BOT_TOKEN=your_bot_token_here
```

### Database Settings

All settings are stored per-group in the SQLite database and persist across bot restarts.

## Troubleshooting 🔍

**Bot not responding?**
- Check if the bot token is correct in `.env`
- Ensure the bot is added to the group
- Verify the bot has admin permissions

**Messages not being deleted?**
- Make sure the bot is an admin in the group
- Check that the feature is enabled in settings

**Settings not saving?**
- Ensure the bot has write permissions to the directory
- Check that `bot_database.db` is being created

## Requirements 💻

- Python 3.8+
- python-telegram-bot 20.7
- python-dotenv 1.0.0
- aiosqlite 0.19.0

## Security Notes 🔒

- Never share your bot token publicly
- The `.env` file contains sensitive credentials
- Keep your `bot_database.db` secure as it contains group data

## License 📄

This project is provided as-is for educational and practical use.

## Support 💬

For issues or questions, check the code comments or review the Telegram Bot API documentation.

---

**Enjoy your well-moderated Telegram groups!** 🎉
# Security Bot 🛡️

Advanced Telegram Group Moderation Bot with auto-restart, global ban system, and comprehensive moderation features.

## ✨ Features

### Moderation Features
- 🚫 **Sticker Blocking** - Automatically delete sticker messages
- ⭐ **Premium Sticker Blocking** - Block premium animated stickers
- 📸 **Media Blocking** - Block photos, videos, documents, etc.
- ↗️ **Forward Blocking** - Block forwarded messages
- 🔗 **Link Blocking** - Block URLs and links
- ⌨️ **Command Blocking** - Block user commands in groups
- 📢 **Channel Post Blocking** - Block posts from channels (allows anonymous admin posts)

### Member Management
- ✅ **Free/Approval System** - Exempt trusted members from restrictions
- 🎛️ **Customizable Exemptions** - Toggle exemptions per user for each restriction type
- 👥 **Bulk Operations** - Remove all approved members at once

### Maintenance & Safety
- 🔄 **Auto-Restart** - Automatically restarts on crash
- 🚫 **Global Ban System** - Ban users across all groups (owner only)
- 📊 **Status Monitoring** - Track uptime, restarts, and bans
- 📝 **Comprehensive Logging** - All events logged to channel
- 🛡️ **Crash Recovery** - Detects and recovers from crashes automatically

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/nishkarshk212/Security-bot.git
cd Security-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env  # or use any text editor
```

Your `.env` file should contain:
```env
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_user_id
LOG_CHANNEL_ID=-100xxxxxxxxx
```

⚠️ **Important:** Never commit your `.env` file with real credentials!

4. **Start the bot**

**Option 1: With auto-restart (Recommended)**
```bash
chmod +x auto_restart.sh
./auto_restart.sh start
```

**Option 2: Normal start**
```bash
python bot.py
```

## 📋 Commands

### User Commands
- `/start` - Start the bot
- `/help` - Show help message
- `/settings` - Open settings panel (admins only)
- `/ping` - Check bot latency

### Admin Commands
- `/free` - Free member from restrictions (reply to message)
- `/unfree` - Remove member from free list
- `/unfreeall` - Remove ALL freed members
- `/freed` - Show freed members count

### Owner Commands
- `/gban` - Globally ban a user (reply to message)
- `/ungban` - Remove global ban
- `/gbanlist` - Show all globally banned users
- `/restart` - Manually restart the bot
- `/status` - Check bot status and uptime

## 🔧 Auto-Restart Script

The `auto_restart.sh` script provides:
- Automatic crash detection and recovery
- Monitoring every 5 seconds
- Crash loop prevention (max 10 restarts in 5 minutes)
- Comprehensive logging

```bash
# Start with monitoring
./auto_restart.sh start

# Check status
./auto_restart.sh status

# Stop bot
./auto_restart.sh stop

# Restart bot
./auto_restart.sh restart
```

## 📁 Project Structure

```
Security-bot/
├── bot.py                 # Main bot file
├── maintenance.py         # Maintenance & global ban system
├── config.py             # Configuration constants
├── font.py               # Text styling utilities
├── auto_restart.sh       # Auto-restart script
├── start_bot.sh          # Simple start script
├── .env.example          # Environment variables template (copy to .env)
├── .env                  # Your actual credentials (DO NOT COMMIT!)
├── requirements.txt      # Python dependencies
├── MAINTENANCE.md        # Maintenance system documentation
├── QUICK_START_MAINTENANCE.md  # Quick reference guide
└── README.md            # This file
```

## 🛠️ Configuration

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Your Telegram bot token | `123456:ABC-DEF...` |
| `OWNER_ID` | Bot owner's Telegram ID | `8791884726` |
| `LOG_CHANNEL_ID` | Channel for logs | `-1003757375746` |

### Getting IDs
- **User ID**: Message @userinfobot on Telegram
- **Channel ID**: Forward a message from channel to @getidsbot

## 📊 Logging

All events are logged to:
- `bot.log` - General bot logs
- `bot_maintenance.log` - Maintenance logs
- `bot_monitor.log` - Auto-restart monitor logs
- Log Channel - Notifications sent to LOG_CHANNEL_ID

## 🔒 Security

- ⚠️ **Never commit your `.env` file** - Use `.env.example` as template
- 🔐 Keep your bot token private
- 👤 Only OWNER_ID can use maintenance commands
- 📝 All maintenance actions are logged
- 🛡️ `.env` is in `.gitignore` to prevent accidental commits

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Nishkarsh Kr**
- GitHub: [@nishkarshk212](https://github.com/nishkarshk212)

## 🙏 Support

If you find this bot helpful, please ⭐ star this repository!

For issues and feature requests, please use the [Issues](https://github.com/nishkarshk212/Security-bot/issues) page.

---

Made with ❤️ for Telegram community
