# Telegram Moderation Bot - Complete Feature Guide

## 🎯 Overview

This bot provides comprehensive group moderation with an intuitive settings panel. All features can be toggled on/off independently and are persisted in a SQLite database.

---

## 📋 Feature List

### 1. 🚫 Sticker Blocking
**What it does:** Automatically deletes all sticker messages from non-admin users.

**Use case:** Keep conversations text-only, prevent sticker spam.

**How it works:**
- Detects incoming sticker messages
- Deletes the message immediately
- Sends a warning to the user (auto-deletes after 3 seconds)

---

### 2. 📸 Media Blocking
**What it does:** Blocks all types of media files including:
- Photos/Images
- Videos
- Documents/Files
- Audio files
- Voice messages
- Video notes
- Animated GIFs

**Use case:** Maintain text-only discussions, prevent large file uploads.

**How it works:**
- Checks for any media attachment in messages
- Deletes media messages instantly
- Notifies the user about the restriction

---

### 3. ↗️ Forward Message Blocking
**What it does:** Prevents users from forwarding messages from other chats/channels.

**Use case:** Ensure original content only, prevent cross-group spam.

**How it works:**
- Detects if a message is forwarded (has `forward_from` attribute)
- Deletes forwarded messages
- Warns the user

---

### 4. 🔗 Link Blocking
**What it does:** Blocks messages containing any URLs including:
- HTTP/HTTPS links
- WWW links
- Telegram.me links
- Any other URL patterns

**Use case:** Prevent external link sharing, reduce spam and phishing attempts.

**How it works:**
- Uses regex pattern matching to detect URLs
- Pattern: `(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)`
- Deletes messages containing links
- Sends warning to user

---

### 5. 🛡️ Spam Protection
**What it does:** Detects and blocks duplicate messages sent by the same user.

**Use case:** Prevent copy-paste spam, repeated promotional messages.

**How it works:**
- Caches message text with user ID and timestamp
- Checks if the same user sent identical message recently
- Default time window: 30 seconds
- Blocks duplicate messages within the time window
- Automatically cleans old cache entries

**Example:**
```
User sends: "Check out this deal!"
Bot: ✅ Allowed (first time)

User sends: "Check out this deal!" (within 30 seconds)
Bot: ❌ Blocked as spam
```

---

### 6. 🌊 Flood Protection
**What it does:** Limits the number of messages a user can send within a specific time window.

**Use case:** Prevent message flooding, rapid-fire spam.

**Available Presets:**
- **3 msgs / 5 seconds** - Strict
- **5 msgs / 10 seconds** - Moderate (Default)
- **7 msgs / 15 seconds** - Relaxed
- **10 msgs / 20 seconds** - Very Relaxed

**How it works:**
- Tracks message timestamps per user
- Counts messages within the time window
- Blocks when limit is exceeded
- Sends detailed warning with current limits
- Auto-cleans old records (2x time window)

**Example (5 msgs/10s setting):**
```
User sends 5 messages in 8 seconds → ✅ All allowed
User sends 6th message at 9 seconds → ❌ Blocked (flood detected)
Warning: "Max 5 messages in 10 seconds"
```

---

## ⚙️ Settings Panel

### Access
- Command: `/settings`
- Permission: Group admins only
- Interface: Interactive inline keyboard

### Features

#### Toggle Buttons
Each feature has a toggle button showing current status:
- ✅ = Enabled
- ❌ = Disabled

Tap any button to toggle that feature on/off.

#### Flood Adjustment
Click the flood settings button to access preset options:
```
🌊 Adjust Flood Protection

Select how many messages allowed in time window:

Current: 5 messages in 10 seconds

[3 msgs/5s] [5 msgs/10s]
[7 msgs/15s] [10 msgs/20s]
[◀️ Back]
```

#### Refresh Button
Updates the settings display to show current state.

#### Close Button
Closes the settings panel.

---

## 👥 User Permissions

### Admin Users
- Can access `/settings` command
- Bypass all moderation restrictions
- Can send stickers, media, links, forwards
- Immune to spam and flood protection

### Regular Users
- Subject to all enabled restrictions
- Cannot modify settings
- Receive warnings when blocked
- Messages deleted automatically

### Bot Messages
- Always bypass restrictions
- Won't trigger moderation

---

## 🤖 Bot Commands

### `/start`
**Description:** Initialize the bot and view welcome message

**Response:**
- Shows bot introduction
- Lists available features
- Provides quick start guide

### `/settings`
**Description:** Open interactive settings panel

**Permission:** Admins only

**Response:**
- Displays current settings status
- Shows inline keyboard with toggles
- Allows real-time configuration

### `/help`
**Description:** Display comprehensive help information

**Response:**
- Lists all commands
- Explains each feature
- Provides usage examples

---

## 💾 Database Structure

### Tables

#### 1. `group_settings`
Stores configuration for each group/chat.

| Column | Type | Description |
|--------|------|-------------|
| chat_id | INTEGER | Primary key, Telegram chat ID |
| block_stickers | BOOLEAN | Sticker blocking on/off |
| block_media | BOOLEAN | Media blocking on/off |
| block_forwards | BOOLEAN | Forward blocking on/off |
| block_links | BOOLEAN | Link blocking on/off |
| spam_protection | BOOLEAN | Spam protection on/off |
| flood_protection | BOOLEAN | Flood protection on/off |
| flood_messages_count | INTEGER | Max messages allowed |
| flood_time_window | INTEGER | Time window in seconds |
| created_at | TIMESTAMP | When settings were created |
| updated_at | TIMESTAMP | Last modification time |

#### 2. `user_messages`
Tracks message timestamps for flood detection.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| chat_id | INTEGER | Chat where message was sent |
| user_id | INTEGER | User who sent the message |
| message_time | TIMESTAMP | When message was sent |

#### 3. `spam_cache`
Caches recent messages for spam detection.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| chat_id | INTEGER | Chat where message was sent |
| user_id | INTEGER | User who sent the message |
| message_text | TEXT | Content of the message |
| message_time | TIMESTAMP | When message was sent |

---

## 🔧 Technical Details

### Moderation Flow

```
Message Received
    ↓
Is it a group? → No → Ignore
    ↓ Yes
Is sender a bot? → Yes → Ignore
    ↓ No
Get group settings
    ↓
Is sender admin? → Yes → Allow
    ↓ No
Check Flood Protection (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Check Spam Protection (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Check Sticker Blocking (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Check Media Blocking (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Check Forward Blocking (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Check Link Blocking (if enabled)
    ↓ Violation
Delete + Warn
    ↓ Pass
Allow Message ✅
```

### Error Handling

- All delete operations wrapped in try-except
- Failed deletions are silently ignored
- Warning messages also have error handling
- Bot continues running even if individual operations fail

### Performance Optimization

- Old message records cleaned up automatically
- Spam cache uses time-based expiration
- Database queries use parameterized statements
- Async/await for non-blocking operations

---

## 🚀 Deployment

### Local Development
```bash
python bot.py
```

### Production (with nohup)
```bash
nohup python bot.py > bot.log 2>&1 &
```

### With Start Script
```bash
./start_bot.sh
```

---

## 🔒 Security Considerations

1. **Bot Token Protection**
   - Stored in `.env` file
   - Never commit `.env` to version control
   - Use environment variables in production

2. **Database Security**
   - SQLite file contains group data
   - Set appropriate file permissions
   - Regular backups recommended

3. **Admin Verification**
   - Bot checks admin status via Telegram API
   - Only verified admins can change settings
   - Admin status checked per-operation

4. **Rate Limiting**
   - Flood protection prevents abuse
   - Warning messages auto-delete
   - Reduces notification spam

---

## 📊 Monitoring & Debugging

### Check Bot Status
```bash
ps aux | grep bot.py
```

### View Logs
```bash
tail -f bot.log
```

### Database Inspection
```bash
sqlite3 bot_database.db
.tables
SELECT * FROM group_settings;
```

### Common Issues

**Issue:** Bot not deleting messages
**Solution:** Ensure bot has admin privileges with delete permission

**Issue:** Settings not persisting
**Solution:** Check write permissions on directory, verify database file exists

**Issue:** Bot crashes on startup
**Solution:** Verify BOT_TOKEN in .env, check internet connection

---

## 🎨 Customization

### Modify Flood Presets
Edit `_show_flood_adjustment()` method in `bot.py`:
```python
keyboard = [
    [InlineKeyboardButton("Custom msgs/s", callback_data="flood_X_Y")],
]
```

### Change Warning Messages
Edit warning texts in `moderate_message()` method.

### Add New Features
1. Add column to `group_settings` table
2. Create toggle handler in `callback_handler()`
3. Add check in `moderate_message()`
4. Update settings panel UI

---

## 📝 Best Practices

1. **Start with moderate settings** - Don't enable all features at once
2. **Monitor user feedback** - Adjust based on group needs
3. **Test in private group first** - Before deploying to large groups
4. **Regular backups** - Backup `bot_database.db` periodically
5. **Update regularly** - Keep dependencies up to date

---

## 🆘 Support

For issues or questions:
1. Check this documentation
2. Review code comments in `bot.py`
3. Check Telegram Bot API documentation
4. Verify bot token and permissions

---

**Happy Moderating!** 🎉
