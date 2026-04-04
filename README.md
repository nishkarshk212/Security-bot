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
# Security-bot
