"""
Advanced Telegram Group Moderation Bot
Features: Sticker blocking, Media blocking, Forward blocking, Link blocking
With member approval system, auto-restart, and global ban
"""

import os
import re
import time
import asyncio
import random
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)
import aiosqlite
from font import Fonts
from config import START_IMG_URL
from maintenance import maintenance_manager, OWNER_ID, LOG_CHANNEL_ID

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Helper function to apply smallcap font
def style_text(text):
    """Apply smallcap font styling to text"""
    return Fonts.smallcap(text)

# Database file
DB_FILE = "bot_database.db"


class DatabaseManager:
    """Manages SQLite database for group settings"""
    
    def __init__(self, db_file):
        self.db_file = db_file
    
    async def initialize(self):
        """Initialize database and create tables if they don't exist"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS group_settings (
                    chat_id INTEGER PRIMARY KEY,
                    block_stickers BOOLEAN DEFAULT 0,
                    block_media BOOLEAN DEFAULT 0,
                    block_forwards BOOLEAN DEFAULT 0,
                    block_links BOOLEAN DEFAULT 0,
                    block_commands BOOLEAN DEFAULT 0,
                    block_premium_stickers BOOLEAN DEFAULT 0,
                    block_channel_posts BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS approved_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    first_name TEXT,
                    approved_by INTEGER,
                    exempt_stickers BOOLEAN DEFAULT 1,
                    exempt_media BOOLEAN DEFAULT 1,
                    exempt_forwards BOOLEAN DEFAULT 0,
                    exempt_links BOOLEAN DEFAULT 0,
                    exempt_commands BOOLEAN DEFAULT 0,
                    exempt_premium_stickers BOOLEAN DEFAULT 1,
                    exempt_channel_posts BOOLEAN DEFAULT 0,
                    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, user_id)
                )
            ''')
            
            # Migration: Add columns if they don't exist
            try:
                await db.execute('ALTER TABLE approved_users ADD COLUMN exempt_premium_stickers BOOLEAN DEFAULT 1')
            except:
                pass
            
            try:
                await db.execute('ALTER TABLE approved_users ADD COLUMN exempt_channel_posts BOOLEAN DEFAULT 0')
            except:
                pass
            
            await db.commit()
    
    async def get_settings(self, chat_id):
        """Get settings for a specific chat"""
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'SELECT * FROM group_settings WHERE chat_id = ?',
                (chat_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    'chat_id': row[0],
                    'block_stickers': bool(row[1]),
                    'block_media': bool(row[2]),
                    'block_forwards': bool(row[3]),
                    'block_links': bool(row[4]),
                    'block_commands': bool(row[5]),
                    'block_premium_stickers': bool(row[6]),
                    'block_channel_posts': bool(row[7]),
                }
            else:
                # Create default settings
                await self.initialize_settings(chat_id)
                return await self.get_settings(chat_id)
    
    async def initialize_settings(self, chat_id):
        """Initialize default settings for a new chat"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                '''INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)''',
                (chat_id,)
            )
            await db.commit()
    
    async def update_setting(self, chat_id, setting_name, value):
        """Update a specific setting"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                f'''UPDATE group_settings SET {setting_name} = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE chat_id = ?''',
                (value, chat_id)
            )
            await db.commit()
    
    async def add_approved_user(self, chat_id, user_id, username, first_name, approved_by):
        """Add user to approved list with default exemptions"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                '''INSERT OR REPLACE INTO approved_users 
                   (chat_id, user_id, username, first_name, approved_by, 
                    exempt_stickers, exempt_media, exempt_forwards, exempt_links, exempt_commands, exempt_premium_stickers, exempt_channel_posts, approved_at) 
                   VALUES (?, ?, ?, ?, ?, 1, 1, 0, 0, 0, 1, 0, CURRENT_TIMESTAMP)''',
                (chat_id, user_id, username, first_name, approved_by)
            )
            await db.commit()
    
    async def update_user_exemptions(self, chat_id, user_id, exempt_stickers, exempt_media, exempt_forwards, exempt_links, exempt_commands, exempt_premium_stickers, exempt_channel_posts):
        """Update user's exemption settings"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                '''UPDATE approved_users 
                   SET exempt_stickers = ?, exempt_media = ?, 
                       exempt_forwards = ?, exempt_links = ?, exempt_commands = ?,
                       exempt_premium_stickers = ?, exempt_channel_posts = ?
                   WHERE chat_id = ? AND user_id = ?''',
                (exempt_stickers, exempt_media, exempt_forwards, exempt_links, exempt_commands, exempt_premium_stickers, exempt_channel_posts, chat_id, user_id)
            )
            await db.commit()
    
    async def get_user_exemptions(self, chat_id, user_id):
        """Get user's exemption settings"""
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'SELECT exempt_stickers, exempt_media, exempt_forwards, exempt_links, exempt_commands, exempt_premium_stickers, exempt_channel_posts FROM approved_users WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    'exempt_stickers': bool(row[0]),
                    'exempt_media': bool(row[1]),
                    'exempt_forwards': bool(row[2]),
                    'exempt_links': bool(row[3]),
                    'exempt_commands': bool(row[4]),
                    'exempt_premium_stickers': bool(row[5]),
                    'exempt_channel_posts': bool(row[6]),
                }
            return None
    
    async def remove_approved_user(self, chat_id, user_id):
        """Remove user from approved list"""
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'DELETE FROM approved_users WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            await db.commit()
    
    async def is_user_approved(self, chat_id, user_id):
        """Check if user is approved"""
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'SELECT COUNT(*) FROM approved_users WHERE chat_id = ? AND user_id = ?',
                (chat_id, user_id)
            )
            count = await cursor.fetchone()
            return count[0] > 0
    
    async def get_approved_users_count(self, chat_id):
        """Get count of approved users in a chat"""
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'SELECT COUNT(*) FROM approved_users WHERE chat_id = ?',
                (chat_id,)
            )
            count = await cursor.fetchone()
            return count[0]
    
    async def unapprove_all_users(self, chat_id):
        """Remove all approved users from a chat"""
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'SELECT COUNT(*) FROM approved_users WHERE chat_id = ?',
                (chat_id,)
            )
            count = await cursor.fetchone()
            await db.execute(
                'DELETE FROM approved_users WHERE chat_id = ?',
                (chat_id,)
            )
            await db.commit()
            return count[0]


class ModerationBot:
    """Main bot class handling all moderation features"""
    
    def __init__(self):
        self.db = DatabaseManager(DB_FILE)
        self.app = None
    
    async def send_auto_delete_message(self, message_obj, text, delete_after=60, **kwargs):
        """Send a message that auto-deletes after specified seconds (default 60)"""
        try:
            sent_message = await message_obj.reply_text(text, **kwargs)
            # Schedule deletion after specified time
            if sent_message:
                asyncio.create_task(self._delete_message_later(sent_message, delete_after))
            return sent_message
        except Exception as e:
            # If reply fails (message deleted), try sending as regular message
            try:
                # Get the chat from the message object
                chat = message_obj.chat if hasattr(message_obj, 'chat') else None
                if chat:
                    sent_message = await self.app.bot.send_message(chat_id=chat.id, text=text, **kwargs)
                    if sent_message:
                        asyncio.create_task(self._delete_message_later(sent_message, delete_after))
                    return sent_message
            except Exception as e2:
                print(f"Error sending auto-delete message: {e2}")
            return None
    
    async def _delete_message_later(self, message, delay):
        """Delete a message after specified delay"""
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except Exception as e:
            # Message might already be deleted or bot lacks permissions
            pass
    
    async def initialize(self):
        """Initialize the bot application"""
        await self.db.initialize()
        
        self.app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        self._add_handlers()
    
    def _add_handlers(self):
        """Add all command and message handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("free", self.cmd_approve))
        self.app.add_handler(CommandHandler("unfree", self.cmd_unapprove))
        self.app.add_handler(CommandHandler("unfreeall", self.cmd_unapproveall))
        self.app.add_handler(CommandHandler("freed", self.cmd_approved))
        self.app.add_handler(CommandHandler("ping", self.cmd_ping))
        
        # Maintenance commands (owner only)
        for handler in maintenance_manager.get_handlers():
            self.app.add_handler(handler)
        
        # Callback queries for inline keyboard
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))
        
        # Message handlers for moderation
        self.app.add_handler(MessageHandler(filters.ALL, self.moderate_message), group=1)
    
    async def _is_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
        """Check if a user is an admin or creator of the chat, handling anonymous admins"""
        chat = update.effective_chat
        user = update.effective_user
        message = update.effective_message or (update.callback_query.message if update.callback_query else None)
        
        if not chat:
            return False
            
        if chat.type not in ['group', 'supergroup']:
            return True  # Always allow in private chats (if the command is meant for private)
            
        # 1. Check if it's an anonymous admin or the group itself via sender_chat
        # In groups, anonymous admins have sender_chat equal to the group chat
        if message and message.sender_chat and message.sender_chat.id == chat.id:
            return True
            
        # 2. Check if it's the anonymous bot (1087968824)
        if user and user.id == 1087968824:
            return True
            
        # 3. Check if it's a message from the group itself (sometimes from_user is None)
        if message and not user and message.sender_chat and message.sender_chat.id == chat.id:
            return True
            
        # 4. Standard admin check
        target_user_id = user_id or (user.id if user else None)
        
        # Special case: 777000 is Telegram service, usually considered admin in group context
        if target_user_id == 777000:
            return True
            
        if not target_user_id:
            # If we still don't have a user ID but it's a message from a chat, it might be an admin
            if message and message.sender_chat:
                # If it's the group itself, already handled. If it's another chat, probably not admin.
                return message.sender_chat.id == chat.id
            return False
            
        try:
            chat_member = await context.bot.get_chat_member(chat.id, target_user_id)
            return chat_member.status in ['creator', 'administrator']
        except Exception:
            return False

    async def can_user_configure_settings(self, chat_id, user_id, context): 
        """Check if a user can configure settings (Owner, Creator, or Admin with Change Info + Ban perms).""" 
        if not user_id: return False 
        
        # Anonymous admins are allowed to configure settings as we can't check specific rights easily 
        ANONYMOUS_ADMIN_ID = 1087968824 
        if user_id == ANONYMOUS_ADMIN_ID: 
            return True 
            
        if user_id == OWNER_ID: 
            return True 
        try: 
            member = await context.bot.get_chat_member(chat_id, user_id) 
            if member.status == 'creator': 
                return True 
            if member.status == 'administrator': 
                # Check for both "Change Group Info" and "Ban Users" (can_restrict_members) 
                return member.can_change_info and member.can_restrict_members 
            return False 
        except: 
            return False

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Get bot username for clickable mention
        bot_username = context.bot.username
        
        if chat.type in ['group', 'supergroup']:
            text = style_text(
                f"๏ ᴛʜɪs ɪs {context.bot.first_name}\n\n"
                "➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
                "ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
                "➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
                "➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂"
            )
            
            keyboard = [
                [InlineKeyboardButton("ʜᴇʟᴘ 🥀", callback_data="help_button")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_video(
                video=random.choice(START_IMG_URL),
                caption=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            text = style_text(
                f"๏ ᴛʜɪs ɪs {context.bot.first_name}\n\n"
                "➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
                "ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
                "➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
                "➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        "ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ 🥀",
                        url=f"https://t.me/{bot_username}?startgroup=true"
                    )
                ],
                [
                    InlineKeyboardButton("ʜᴇʟᴘ 🥀", callback_data="help_button")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_video(
                video=random.choice(START_IMG_URL),
                caption=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = style_text(
            "📚 Bot Commands & Features\n\n"
            "Commands:\n"
            "/start - Start the bot\n"
            "/settings - Open settings panel\n"
            "/free - Free member from restrictions (reply to message)\n"
            "/unfree - Remove member from free list (reply to message)\n"
            "/unfreeall - Remove ALL freed members\n"
            "/freed - Show freed members count\n"
            "/ping - Check bot latency\n"
            "/help - Show this help message\n\n"
            "Moderation Features:\n\n"
            "🚫 Sticker Blocking\n"
            "Automatically delete sticker messages\n\n"
            "⭐ Premium Sticker Blocking\n"
            "Block premium animated stickers from Telegram Premium\n\n"
            "📸 Media Blocking\n"
            "Block photos, videos, documents, audio, voice messages\n\n"
            "↗️ Forward Blocking\n"
            "Prevent users from forwarding messages from other chats\n\n"
            "🔗 Link Blocking\n"
            "Block messages containing URLs (Telegram links, external links)\n\n"
            "⌨️ Command Blocking\n"
            "Block messages starting with / or ! (custom commands)\n\n"
            "📢 Channel Post Blocking\n"
            "Block messages sent from channels (anonymous channel posts)\n\n"
            "✅ Member Approval System\n"
            "Free trusted members to exempt them from restrictions.\n"
            "Configure exemptions for stickers, media, forwards, links, and commands.\n\n"
            "How to Free Members:\n"
            "1. Reply to a member's message\n"
            "2. Use /free command\n"
            "3. Tap buttons to configure exemptions\n\n"
            "Note: Only admins can change settings and free members."
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='HTML'
        )
    
    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command - Show settings panel"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user has required admin permissions
        if chat.type in ['group', 'supergroup']:
            user_id = user.id if user else None
            if not user_id:
                # Handle anonymous admin via sender_chat
                is_admin = await self._is_admin(update, context)
                if not is_admin:
                    await self.send_auto_delete_message(
                        update.message,
                        style_text("❌ Only group admins can access settings."),
                        delete_after=60,
                        parse_mode='HTML'
                    )
                    return
            else:
                # Use stricter permission check for named users
                can_configure = await self.can_user_configure_settings(chat.id, user_id, context)
                if not can_configure:
                    await self.send_auto_delete_message(
                        update.message,
                        style_text("❌ You need ban users and change group info permissions to access settings."),
                        delete_after=60,
                        parse_mode='HTML'
                    )
                    return
        
        # Get current settings
        settings = await self.db.get_settings(chat.id)
        
        # Create settings panel
        keyboard = self._create_settings_keyboard(settings)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = self._format_settings_text(settings)
        
        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    def _create_settings_keyboard(self, settings):
        """Create inline keyboard for settings with grid layout"""
        keyboard = [
            # Row 1: Stickers & Media
            [
                InlineKeyboardButton(
                    f"{'✅' if settings['block_stickers'] else '❌'} 🚫 Stickers",
                    callback_data="toggle_block_stickers"
                ),
                InlineKeyboardButton(
                    f"{'✅' if settings['block_media'] else '❌'} 📸 Media",
                    callback_data="toggle_block_media"
                ),
            ],
            # Row 2: Forwards & Links
            [
                InlineKeyboardButton(
                    f"{'✅' if settings['block_forwards'] else '❌'} ↗️ Forwards",
                    callback_data="toggle_block_forwards"
                ),
                InlineKeyboardButton(
                    f"{'✅' if settings['block_links'] else '❌'} 🔗 Links",
                    callback_data="toggle_block_links"
                ),
            ],
            # Row 3: Commands & Premium Stickers
            [
                InlineKeyboardButton(
                    f"{'✅' if settings['block_commands'] else '❌'} ⌨️ Commands",
                    callback_data="toggle_block_commands"
                ),
                InlineKeyboardButton(
                    f"{'✅' if settings['block_premium_stickers'] else '❌'} ⭐ Premium Stickers",
                    callback_data="toggle_block_premium_stickers"
                ),
            ],
            # Row 4: Channel Posts
            [
                InlineKeyboardButton(
                    f"{'✅' if settings['block_channel_posts'] else '❌'} 📢 Channel Posts",
                    callback_data="toggle_block_channel_posts"
                ),
            ],
            # Row 5: Action Buttons
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_settings"),
                InlineKeyboardButton("❌ Close", callback_data="close_settings"),
            ],
        ]
        return keyboard
    
    def _create_approval_keyboard(self, exemptions, user_id):
        """Create 6-button grid for exemption selection with close button"""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_stickers'] else '❌'} 🚫 Stickers",
                    callback_data=f"exempt_stickers_{user_id}"
                ),
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_media'] else '❌'} 📸 Media",
                    callback_data=f"exempt_media_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_forwards'] else '❌'} ↗️ Forwards",
                    callback_data=f"exempt_forwards_{user_id}"
                ),
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_links'] else '❌'} 🔗 Links",
                    callback_data=f"exempt_links_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_commands'] else '❌'} ⌨️ Commands",
                    callback_data=f"exempt_commands_{user_id}"
                ),
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_premium_stickers'] else '❌'} ⭐ Premium Stickers",
                    callback_data=f"exempt_premium_stickers_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if exemptions['exempt_channel_posts'] else '❌'} 📢 Channel Posts",
                    callback_data=f"exempt_channel_posts_{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Close",
                    callback_data="close_approval"
                ),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _format_settings_text(self, settings):
        """Format settings into readable text"""
        status_emoji = lambda x: "✅ Enabled" if x else "❌ Disabled"
        
        text = style_text(
            "⚙️ Group Moderation Settings\n\n"
            f"🚫 Block Stickers: {status_emoji(settings['block_stickers'])}\n"
            f"📸 Block Media: {status_emoji(settings['block_media'])}\n"
            f"↗️ Block Forwards: {status_emoji(settings['block_forwards'])}\n"
            f"🔗 Block Links: {status_emoji(settings['block_links'])}\n"
            f"⌨️ Block Commands: {status_emoji(settings['block_commands'])}\n"
            f"⭐ Block Premium Stickers: {status_emoji(settings['block_premium_stickers'])}\n"
            f"📢 Block Channel Posts: {status_emoji(settings['block_channel_posts'])}\n\n"
            "Tap buttons above to toggle features.\n"
            "Use /free to exempt members from restrictions."
        )
        
        return text
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button clicks"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        data = query.data
        
        # Handle close
        if data == "close_settings":
            await query.message.delete()
            return
        
        # Handle help button from start message
        if data == "help_button":
            help_text = style_text(
                "📚 Bot Commands & Features\n\n"
                "Commands:\n"
                "/start - Start the bot\n"
                "/settings - Open settings panel\n"
                "/free - Free member from restrictions (reply to message)\n"
                "/unfree - Remove member from free list (reply to message)\n"
                "/unfreeall - Remove ALL freed members\n"
                "/freed - Show freed members count\n"
                "/ping - Check bot latency\n"
                "/help - Show this help message\n\n"
                "Moderation Features:\n\n"
                "🚫 Sticker Blocking\n"
                "Automatically delete sticker messages\n\n"
                "⭐ Premium Sticker Blocking\n"
                "Block premium animated stickers from Telegram Premium\n\n"
                "📸 Media Blocking\n"
                "Block photos, videos, documents, audio, voice messages\n\n"
                "↗️ Forward Blocking\n"
                "Prevent users from forwarding messages from other chats\n\n"
                "🔗 Link Blocking\n"
                "Block messages containing URLs (Telegram links, external links)\n\n"
                "⌨️ Command Blocking\n"
                "Block messages starting with / or ! (custom commands)\n\n"
                "📢 Channel Post Blocking\n"
                "Block messages sent from channels (anonymous channel posts)\n\n"
                "✅ Member Approval System\n"
                "Approve trusted members to exempt them from restrictions.\n"
                "Configure exemptions for stickers, media, forwards, links, and commands.\n\n"
                "How to Free Members:\n"
                "1. Reply to a member's message\n"
                "2. Use /free command\n"
                "3. Tap buttons to configure exemptions\n\n"
                "Note: Only admins can change settings and free members."
            )
            
            await query.message.reply_text(
                help_text,
                parse_mode='HTML'
            )
            await query.answer()
            return
        
        # Handle exemption toggles
        if data.startswith("exempt_"):
            # Check if user has required admin permissions
            is_admin = await self._is_admin(update, context)
            if not is_admin:
                await query.answer(style_text("❌ Only admins can toggle exemptions"), show_alert=True)
                return
                
            # Parse callback data
            if data.startswith("exempt_premium_stickers_"):
                exemption_type = "premium_stickers"
                target_user_id = int(data.replace("exempt_premium_stickers_", ""))
            elif data.startswith("exempt_channel_posts_"):
                exemption_type = "channel_posts"
                target_user_id = int(data.replace("exempt_channel_posts_", ""))
            else:
                parts = data.split("_")
                exemption_type = parts[1]
                target_user_id = int(parts[2])
            
            # Get current exemptions
            exemptions = await self.db.get_user_exemptions(chat_id, target_user_id)
            if not exemptions:
                await query.answer(style_text("User not found in approved list."), show_alert=True)
                return
            
            # Toggle the specific exemption
            new_value = not exemptions[f'exempt_{exemption_type}']
            exemptions[f'exempt_{exemption_type}'] = new_value
            
            # Update database
            await self.db.update_user_exemptions(
                chat_id,
                target_user_id,
                exemptions['exempt_stickers'],
                exemptions['exempt_media'],
                exemptions['exempt_forwards'],
                exemptions['exempt_links'],
                exemptions['exempt_commands'],
                exemptions['exempt_premium_stickers'],
                exemptions['exempt_channel_posts']
            )
            
            # Update keyboard
            keyboard = self._create_approval_keyboard(exemptions, target_user_id)
            
            try:
                await query.message.edit_reply_markup(reply_markup=keyboard)
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
            
            status = "enabled" if new_value else "disabled"
            await query.answer(style_text(f"{exemption_type.capitalize()} exemption {status}"))
            return
        
        # Handle close approval settings
        if data == "close_approval":
            await query.message.delete()
            return
        
        # Handle refresh
        if data == "refresh_settings":
            settings = await self.db.get_settings(chat_id)
            keyboard = self._create_settings_keyboard(settings)
            reply_markup = InlineKeyboardMarkup(keyboard)
            settings_text = self._format_settings_text(settings)
            
            try:
                await query.message.edit_text(
                    settings_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                if "Message is not modified" not in str(e):
                    raise
            return
        
        # Handle toggle settings
        if data.startswith("toggle_"):
            # Check if user has required admin permissions
            user_id = query.from_user.id if query.from_user else None
            if not user_id:
                # Handle anonymous admin via sender_chat
                is_admin = await self._is_admin(update, context)
                if not is_admin:
                    await query.answer(style_text("❌ Only admins can change settings"), show_alert=True)
                    return
            else:
                # Use stricter permission check for named users
                can_configure = await self.can_user_configure_settings(chat_id, user_id, context)
                if not can_configure:
                    await query.answer(
                        style_text("❌ You need ban users and change group info permissions to change settings"),
                        show_alert=True
                    )
                    return
            
            setting_name = data.replace("toggle_", "")
            settings = await self.db.get_settings(chat_id)
            current_value = settings.get(setting_name, False)
            new_value = not current_value
            
            await self.db.update_setting(chat_id, setting_name, int(new_value))
            
            # Show confirmation
            status = "enabled" if new_value else "disabled"
            feature_names = {
                'block_stickers': 'Sticker Blocking',
                'block_media': 'Media Blocking',
                'block_forwards': 'Forward Blocking',
                'block_links': 'Link Blocking',
                'block_commands': 'Command Blocking',
                'block_premium_stickers': 'Premium Sticker Blocking',
                'block_channel_posts': 'Channel Post Blocking',
            }
            
            feature_name = feature_names.get(setting_name, setting_name)
            confirmation_msg = await query.message.reply_text(
                style_text(f"✅ {feature_name} has been {status}."),
                parse_mode='HTML'
            )
            
            # Auto-delete confirmation after 60 seconds
            asyncio.create_task(self._delete_message_later(confirmation_msg, 60))
            
            # Refresh settings panel
            settings = await self.db.get_settings(chat_id)
            keyboard = self._create_settings_keyboard(settings)
            reply_markup = InlineKeyboardMarkup(keyboard)
            settings_text = self._format_settings_text(settings)
            
            await query.message.edit_text(
                settings_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def _resolve_target_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Helper to resolve target user from reply, mentions, or arguments"""
        chat = update.effective_chat
        message = update.message
        
        # 1. Check reply
        if message.reply_to_message:
            return message.reply_to_message.from_user
            
        # 2. Check all entities for text_mention (provides User object)
        if message.entities:
            for entity in message.entities:
                if entity.type == 'text_mention' and entity.user:
                    return entity.user
        
        # 3. Check arguments for ID or Username
        if context.args:
            for arg in context.args:
                # Check if it's a numeric User ID
                if arg.isdigit():
                    try:
                        target_user_id = int(arg)
                        chat_member = await context.bot.get_chat_member(chat.id, target_user_id)
                        return chat_member.user
                    except:
                        # Try database if not in chat
                        async with aiosqlite.connect(self.db.db_file) as db:
                            cursor = await db.execute(
                                'SELECT user_id, first_name, username FROM approved_users WHERE chat_id = ? AND user_id = ?',
                                (chat.id, target_user_id)
                            )
                            row = await cursor.fetchone()
                            if row:
                                from telegram import User
                                return User(id=row[0], first_name=row[1], is_bot=False, username=row[2])
                
                # Check if it's a username
                elif arg.startswith('@'):
                    target_username = arg[1:].lower()
                    
                    # Try to find in admins first
                    try:
                        admins = await context.bot.get_chat_administrators(chat.id)
                        for admin in admins:
                            if admin.user.username and admin.user.username.lower() == target_username:
                                return admin.user
                    except:
                        pass
                        
                    # Try database
                    async with aiosqlite.connect(self.db.db_file) as db:
                        cursor = await db.execute(
                            'SELECT user_id, first_name FROM approved_users WHERE chat_id = ? AND LOWER(username) = ?',
                            (chat.id, target_username)
                        )
                        row = await cursor.fetchone()
                        if row:
                            from telegram import User
                            return User(id=row[0], first_name=row[1], is_bot=False, username=target_username)
        
        # 4. Last resort: check any mention entities even if not in args
        if message.entities:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    target_username = mention_text[1:].lower()
                    
                    # Try admins
                    try:
                        admins = await context.bot.get_chat_administrators(chat.id)
                        for admin in admins:
                            if admin.user.username and admin.user.username.lower() == target_username:
                                return admin.user
                    except:
                        pass
                        
                    # Try database
                    async with aiosqlite.connect(self.db.db_file) as db:
                        cursor = await db.execute(
                            'SELECT user_id, first_name FROM approved_users WHERE chat_id = ? AND LOWER(username) = ?',
                            (chat.id, target_username)
                        )
                        row = await cursor.fetchone()
                        if row:
                            from telegram import User
                            return User(id=row[0], first_name=row[1], is_bot=False, username=target_username)
                            
        return None

    async def cmd_approve(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /free command - Free member to bypass restrictions"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user has required admin permissions
        if chat.type in ['group', 'supergroup']:
            is_admin = await self._is_admin(update, context)
            if not is_admin:
                await self.send_auto_delete_message(
                    update.message,
                    style_text("❌ Only group admins can approve members."),
                    delete_after=60,
                    parse_mode='HTML'
                )
                return
            
            # If administrator, check specific permissions
            # Note: For anonymous admins, we allow member approval by default
            if user and user.id != 1087968824: # Not anonymous bot
                try:
                    chat_member = await context.bot.get_chat_member(chat.id, user.id)
                    if chat_member.status == 'administrator':
                        can_restrict = getattr(chat_member, 'can_restrict_members', False)
                        
                        if not can_restrict:
                            await self.send_auto_delete_message(
                                update.message,
                                style_text("❌ You need ban users permission to approve members."),
                                delete_after=60,
                                parse_mode='HTML'
                            )
                            return
                except:
                    pass
        elif chat.type == 'private':
            # Allow in private if needed, but usually /free is for groups
            pass
        else:
            await self.send_auto_delete_message(
                update.message,
                style_text("This command can only be used in groups."),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        # Resolve the target user
        target_user = await self._resolve_target_user(update, context)
        
        if not target_user:
            await self.send_auto_delete_message(
                update.message,
                style_text("ℹ️ <b>How to use /free:</b>\n\n"
                          "1. Reply to a user's message\n"
                          "2. Mention them: <code>/free</code> [click name]\n"
                          "3. Use their User ID: <code>/free 123456789</code>"),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        # Check if already approved
        is_approved = await self.db.is_user_approved(chat.id, target_user.id)
        
        # Don't allow approving the anonymous bot or other system bots
        if target_user.id in [1087968824, 777000]:
            await self.send_auto_delete_message(
                update.message,
                style_text("❌ Cannot approve anonymous admins or system accounts."),
                delete_after=60,
                parse_mode='HTML'
            )
            return
            
        # Get exemptions
        exemptions = await self.db.get_user_exemptions(chat.id, target_user.id)
        if not exemptions:
            # Default exemptions if not in DB yet
            exemptions = {
                'exempt_stickers': True,
                'exempt_media': True,
                'exempt_forwards': False,
                'exempt_links': False,
                'exempt_commands': False,
                'exempt_premium_stickers': True,
                'exempt_channel_posts': False
            }
        
        # Send approval message with 6-button grid
        keyboard = self._create_approval_keyboard(exemptions, target_user.id)
        
        if is_approved:
            approval_text = (
                f"✅ <b>{target_user.mention_html()} is already freed!</b>\n\n"
                f"Current exemption settings:\n\n"
                f"<i>Tap buttons below to toggle exemptions</i>"
            )
        else:
            approved_by_id = user.id if user else 0
            await self.db.add_approved_user(
                chat.id,
                target_user.id,
                target_user.username or "",
                target_user.first_name or "",
                approved_by_id
            )
            approval_text = (
                f"✅ <b>Member Freed!</b>\n\n"
                f"{target_user.mention_html()} can now configure exemptions:\n\n"
                f"<i>Tap buttons below to toggle exemptions</i>"
            )
        
        await update.message.reply_text(
            approval_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    async def cmd_unapprove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unfree command - Remove member from free list"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user has required admin permissions
        if chat.type in ['group', 'supergroup']:
            is_admin = await self._is_admin(update, context)
            if not is_admin:
                await self.send_auto_delete_message(
                    update.message,
                    style_text("❌ Only group admins can unfree members."),
                    delete_after=60,
                    parse_mode='HTML'
                )
                return
        else:
            return
        
        # Resolve the target user
        target_user = await self._resolve_target_user(update, context)
        
        if not target_user:
            await self.send_auto_delete_message(
                update.message,
                style_text("ℹ️ Reply to a user or use <code>/unfree [ID/username]</code>"),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        is_approved = await self.db.is_user_approved(chat.id, target_user.id)
        if not is_approved:
            await self.send_auto_delete_message(
                update.message,
                f"❌ {target_user.mention_html()} is not in the freed list.",
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        await self.db.remove_approved_user(chat.id, target_user.id)
        await self.send_auto_delete_message(
            update.message,
            f"❌ {target_user.mention_html()} has been removed from freed list.",
            delete_after=60,
            parse_mode='HTML'
        )

    
    async def cmd_approved(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /freed command - Show list of freed members"""
        chat = update.effective_chat
        
        if chat.type not in ['group', 'supergroup']:
            await self.send_auto_delete_message(
                update.message,
                style_text("This command can only be used in groups."),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        async with aiosqlite.connect(self.db.db_file) as db:
            cursor = await db.execute(
                'SELECT user_id, first_name, username FROM approved_users WHERE chat_id = ? ORDER BY approved_at DESC',
                (chat.id,)
            )
            rows = await cursor.fetchall()
        
        if not rows:
            await self.send_auto_delete_message(
                update.message,
                style_text("📋 No freed members yet.\n\n"
                "Use /free (reply to message) to exempt members from restrictions."),
                delete_after=60,
                parse_mode='HTML'
            )
        else:
            text = f"📋 <b>Freed Members ({len(rows)}):</b>\n\n"
            for i, row in enumerate(rows[:50], 1):  # Limit to 50 for message length
                user_id, first_name, username = row
                user_text = f"@{username}" if username else first_name
                text += f"{i}. {user_text} (<code>{user_id}</code>)\n"
            
            if len(rows) > 50:
                text += f"\n<i>... and {len(rows) - 50} more.</i>"
            
            text += style_text("\n\nUse /unfree to remove from free list.")
            
            await self.send_auto_delete_message(
                update.message,
                text,
                delete_after=120,
                parse_mode='HTML'
            )
    
    async def cmd_unapproveall(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unfreeall command - Remove all freed members"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Check if user has required admin permissions
        if chat.type in ['group', 'supergroup']:
            is_admin = await self._is_admin(update, context)
            if not is_admin:
                await self.send_auto_delete_message(
                    update.message,
                    style_text("❌ Only group admins can unfree all members."),
                    delete_after=60,
                    parse_mode='HTML'
                )
                return
            
            # If administrator, check specific permissions
            # Note: For anonymous admins, we allow member unapproval by default
            if user and user.id != 1087968824: # Not anonymous bot
                try:
                    chat_member = await context.bot.get_chat_member(chat.id, user.id)
                    if chat_member.status == 'administrator':
                        can_restrict = getattr(chat_member, 'can_restrict_members', False)
                        
                        if not can_restrict:
                            await self.send_auto_delete_message(
                                update.message,
                                style_text("❌ You need ban users permission to unfree all members."),
                                delete_after=60,
                                parse_mode='HTML'
                            )
                            return
                except:
                    pass
        else:
            await self.send_auto_delete_message(
                update.message,
                style_text("This command can only be used in groups."),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        # Get count before deleting
        count = await self.db.get_approved_users_count(chat.id)
        
        if count == 0:
            await self.send_auto_delete_message(
                update.message,
                style_text("📋 No freed members to remove."),
                delete_after=60,
                parse_mode='HTML'
            )
            return
        
        # Unapprove all users
        removed_count = await self.db.unapprove_all_users(chat.id)
        
        await self.send_auto_delete_message(
            update.message,
            style_text(f"✅ All Freed Members Removed!\n\n"
            f"Removed {removed_count} freed member(s).\n"
            f"All members are now subject to group restrictions."),
            delete_after=60,
            parse_mode='HTML'
        )
    
    async def cmd_ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command - Show bot latency"""
        start_time = time.time()
        
        # Send initial ping message
        message = await update.message.reply_text(
            style_text("🏓 Pinging..."),
            parse_mode='HTML'
        )
        
        # Calculate latency
        end_time = time.time()
        latency = round((end_time - start_time) * 1000, 2)
        
        # Edit message with actual ping
        ping_text = style_text(
            f"🏓 Pong!\n\n"
            f"⚡ Latency: {latency}ms\n"
            f"🤖 Bot is online and responding!"
        )
        
        try:
            await message.edit_text(
                text=ping_text,
                parse_mode='HTML'
            )
        except:
            pass
    
    async def moderate_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main message moderation handler"""
        if not update.message or not update.effective_chat:
            return
        
        chat = update.effective_chat
        user = update.effective_user
        message = update.message
        
        # Skip if not a group
        if chat.type not in ['group', 'supergroup']:
            return
        
        # Check global ban first (before any other checks)
        if user and maintenance_manager.is_globally_banned(user.id):
            try:
                await message.delete()
                logger.info(f"🚫 Globally banned user {user.id} blocked in {chat.id}")
            except:
                pass
            return
        
        # Get settings first (needed for other checks)
        settings = await self.db.get_settings(chat.id)
        
        # LOGGING FOR DEBUGGING
        if message.sticker:
            logger.info(f"Sticker detected in {chat.title} ({chat.id}) from {user.first_name if user else 'Unknown'}")
            logger.info(f"Sticker details: is_animated={message.sticker.is_animated}, is_video={message.sticker.is_video}")
            if hasattr(message.sticker, 'premium_animation'):
                logger.info(f"Sticker has premium_animation: {message.sticker.premium_animation is not None}")
            if hasattr(message.sticker, 'custom_emoji_id'):
                logger.info(f"Sticker has custom_emoji_id: {message.sticker.custom_emoji_id}")
        
        # Check custom emoji in text/caption
        entities = list(message.entities or []) + list(message.caption_entities or [])
        for entity in entities:
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                logger.info(f"Custom emoji detected in {chat.title} ({chat.id}) from {user.first_name if user else 'Unknown'}")
                break

        # Check command blocking (skip for users with exemption)
        # We check this EARLY before admin checks so that we can block regular user commands
        # but we need to ensure admins can still use commands.
        if settings['block_commands'] and message.text:
            # Detect commands starting with / or !
            # Also check message.entities for 'bot_command' type
            is_command = False
            if message.text.strip().startswith(('/', '!')):
                is_command = True
            elif message.entities:
                for entity in message.entities:
                    if entity.type == 'bot_command':
                        is_command = True
                        break
            
            if is_command:
                # Now check if the user is an admin or exempt
                is_admin = await self._is_admin(update, context)
                
                if not is_admin:
                    # Check if user is approved and get exemptions
                    is_approved = False
                    exemptions = None
                    if user:
                        is_approved = await self.db.is_user_approved(chat.id, user.id)
                        exemptions = await self.db.get_user_exemptions(chat.id, user.id) if is_approved else None
                    
                    if not (exemptions and exemptions.get('exempt_commands', False)):
                        try:
                            await message.delete()
                            await self.send_auto_delete_message(
                                message,
                                f"⌨️ Commands are not allowed in this group.",
                                delete_after=60,
                                parse_mode='HTML'
                            )
                        except:
                            pass
                        return

        # Check if user is admin or approved (bypass restrictions)
        is_admin = await self._is_admin(update, context)
        if is_admin:
            return
            
        is_approved = False
        exemptions = None
        
        if user:
            # Check if user is approved and get exemptions
            is_approved = await self.db.is_user_approved(chat.id, user.id)
            exemptions = await self.db.get_user_exemptions(chat.id, user.id) if is_approved else None
        
        # Check channel post blocking
        # Only block messages from CHANNELS, allow messages from GROUPS
        # sender_chat can be either a channel or a group
        if settings['block_channel_posts'] and message.sender_chat:
            # Check if sender_chat is a channel (not a group)
            is_channel = message.sender_chat.type == 'channel'
            
            if is_channel:
                # Check if user is approved for channel posts
                if exemptions and exemptions.get('exempt_channel_posts', False):
                    return  # User is exempt
                
                # This is from a channel - BLOCK IT
                print(f"📢 Blocking channel message from: {message.sender_chat.title} (ID: {message.sender_chat.id})")
                try:
                    await message.delete()
                    await self.send_auto_delete_message(
                        message,
                        f"📢 Channel posts are not allowed in this group.",
                        delete_after=60,
                        parse_mode='HTML'
                    )
                    print(f"✅ Channel message deleted successfully")
                except Exception as e:
                    print(f"❌ Error deleting channel message: {e}")
                return
            else:
                # This is from a group - ALLOW IT
                print(f"✅ Allowing group message from: {message.sender_chat.title}")
        
        # Skip bot messages
        if user and user.is_bot:
            return
        
        # Check sticker blocking (skip for users with exemption)
        if message.sticker:
            is_blocked = False
            
            # 1. Detection logic for premium stickers
            is_premium = False
            sticker = message.sticker
            if (hasattr(sticker, 'premium_animation') and sticker.premium_animation) or \
               (hasattr(sticker, 'custom_emoji_id') and sticker.custom_emoji_id):
                is_premium = True
            elif hasattr(sticker, 'type') and sticker.type == 'custom_emoji':
                is_premium = True
            elif hasattr(sticker, 'set_name') and sticker.set_name and sticker.set_name.startswith('emoji'):
                is_premium = True
            
            # 2. Blocking logic for premium stickers
            if is_premium:
                # Block if group blocks premium stickers AND user is not exempt from them
                if settings['block_premium_stickers'] and not (exemptions and exemptions.get('exempt_premium_stickers')):
                    is_blocked = True
                # OR block if group blocks ALL stickers AND user is not exempt from ALL stickers
                elif settings['block_stickers'] and not (exemptions and exemptions.get('exempt_stickers')):
                    is_blocked = True
            
            # 3. Blocking logic for regular stickers
            else:
                if settings['block_stickers'] and not (exemptions and exemptions.get('exempt_stickers')):
                    is_blocked = True
            
            if is_blocked:
                try:
                    await message.delete()
                    await self.send_auto_delete_message(
                        message,
                        f"🚫 Stickers are not allowed in this group.",
                        delete_after=60,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Failed to delete sticker: {e}")
                return
        
        # Check custom emoji blocking (skip for users with exemption)
        # Custom emojis appear in text messages or captions with custom_emoji_id in entities
        if settings['block_stickers'] or settings['block_premium_stickers']:
            entities = list(message.entities or []) + list(message.caption_entities or [])
            has_custom_emoji = False
            for entity in entities:
                if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                    has_custom_emoji = True
                    break
                if entity.type == 'custom_emoji':
                    has_custom_emoji = True
                    break
            
            if has_custom_emoji:
                is_blocked = False
                # Block if group blocks premium stickers AND user is not exempt from them
                if settings['block_premium_stickers'] and not (exemptions and exemptions.get('exempt_premium_stickers')):
                    is_blocked = True
                # OR block if group blocks ALL stickers AND user is not exempt from ALL stickers
                elif settings['block_stickers'] and not (exemptions and exemptions.get('exempt_stickers')):
                    is_blocked = True
                
                if is_blocked:
                    try:
                        await message.delete()
                        await self.send_auto_delete_message(
                            message,
                            f"🚫 Custom emoji stickers are not allowed in this group.",
                            delete_after=60,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.error(f"Failed to delete custom emoji: {e}")
                    return
        
        # Check media blocking (skip for users with exemption)
        if settings['block_media']:
            if any([
                message.photo,
                message.video,
                message.document,
                message.audio,
                message.voice,
                message.video_note,
                message.animation
            ]):
                if exemptions and exemptions['exempt_media']:
                    return  # User is exempt
                try:
                    await message.delete()
                    await self.send_auto_delete_message(
                        message,
                        f"📸 Media files are not allowed in this group.",
                        delete_after=60,
                        parse_mode='HTML'
                    )
                except:
                    pass
                return
        
        # Check forward blocking (skip for users with exemption)
        if settings['block_forwards'] and (message.forward_date or message.forward_origin):
            if exemptions and exemptions['exempt_forwards']:
                return  # User is exempt
            try:
                await message.delete()
                await self.send_auto_delete_message(
                    message,
                    f"↗️ Forwarded messages are not allowed in this group.",
                    delete_after=60,
                    parse_mode='HTML'
                )
            except:
                pass
            return
        
        # Check link blocking (skip for users with exemption)
        if settings['block_links'] and message.text:
            url_pattern = r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)'
            if re.search(url_pattern, message.text):
                if exemptions and exemptions['exempt_links']:
                    return  # User is exempt
                try:
                    await message.delete()
                    await self.send_auto_delete_message(
                        message,
                        f"🔗 Links are not allowed in this group.",
                        delete_after=60,
                        parse_mode='HTML'
                    )
                except:
                    pass
                return
        
        return
    
    async def run(self):
        """Run the bot"""
        print("🤖 Starting Advanced Moderation Bot...")
        print("Press Ctrl+C to stop.")
        
        # Notify about startup
        try:
            await maintenance_manager.notify_restart(self.app.bot, "Bot started/restarted")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
        
        try:
            await self.app.initialize()
            await self.app.start()
            
            # Start polling
            await self.app.updater.start_polling(drop_pending_updates=True)
            
            # Keep running
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                print("\n👋 Bot stopped by user.")
            except Exception as e:
                logger.error(f"Bot crashed: {e}")
                await maintenance_manager.check_and_handle_crash(self.app.bot, e)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            await maintenance_manager.check_and_handle_crash(self.app.bot, e)
        finally:
            try:
                await self.app.stop()
                await self.app.shutdown()
            except:
                pass


import fcntl


async def main():
    """Main entry point"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file!")
        return
    
    # Check for multiple instances on the same machine
    lock_file = open('bot.lock', 'w')
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("❌ Error: Another instance of the bot is already running on this machine.")
        return
    
    bot = ModerationBot()
    await bot.initialize()
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
