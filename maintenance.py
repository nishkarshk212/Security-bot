"""
Maintenance Module - Auto-restart, crash recovery, and global ban system
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from dotenv import load_dotenv

load_dotenv()

# Configuration
OWNER_ID = int(os.getenv('OWNER_ID', '8791884726'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '-1003757375746'))

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_maintenance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MaintenanceManager:
    """Handles bot maintenance, auto-restart, and global ban functionality"""
    
    def __init__(self):
        self.restart_count = 0
        self.last_restart_time = None
        self.global_banned_users = set()
        self.load_global_bans()
    
    def load_global_bans(self):
        """Load global bans from file"""
        try:
            if os.path.exists('global_bans.txt'):
                with open('global_bans.txt', 'r') as f:
                    self.global_banned_users = set(int(line.strip()) for line in f if line.strip())
                logger.info(f"Loaded {len(self.global_banned_users)} global bans")
        except Exception as e:
            logger.error(f"Error loading global bans: {e}")
            self.global_banned_users = set()
    
    def save_global_bans(self):
        """Save global bans to file"""
        try:
            with open('global_bans.txt', 'w') as f:
                for user_id in self.global_banned_users:
                    f.write(f"{user_id}\n")
            logger.info(f"Saved {len(self.global_banned_users)} global bans")
        except Exception as e:
            logger.error(f"Error saving global bans: {e}")
    
    def is_globally_banned(self, user_id: int) -> bool:
        """Check if user is globally banned"""
        return user_id in self.global_banned_users
    
    def add_global_ban(self, user_id: int) -> bool:
        """Add user to global ban list"""
        if user_id not in self.global_banned_users:
            self.global_banned_users.add(user_id)
            self.save_global_bans()
            return True
        return False
    
    def remove_global_ban(self, user_id: int) -> bool:
        """Remove user from global ban list"""
        if user_id in self.global_banned_users:
            self.global_banned_users.remove(user_id)
            self.save_global_bans()
            return True
        return False
    
    async def log_to_channel(self, bot, message: str):
        """Send log message to log channel"""
        try:
            await bot.send_message(
                chat_id=LOG_CHANNEL_ID,
                text=f"📋 **Bot Log**\n\n{message}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send log to channel: {e}")
    
    async def notify_restart(self, bot, reason: str = "Unknown"):
        """Notify owner and log channel about restart"""
        self.restart_count += 1
        self.last_restart_time = datetime.now()
        
        message = (
            f"🔄 **Bot Restarted**\n\n"
            f"**Reason:** {reason}\n"
            f"**Restart Count:** {self.restart_count}\n"
            f"**Time:** {self.last_restart_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Log to channel
        await self.log_to_channel(bot, message)
        
        # Notify owner
        try:
            await bot.send_message(
                chat_id=OWNER_ID,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify owner: {e}")
        
        logger.info(f"Bot restarted: {reason}")
    
    async def check_and_handle_crash(self, bot, error: Exception):
        """Handle bot crash and schedule restart"""
        error_msg = str(error)
        logger.error(f"Bot crash detected: {error_msg}")
        
        # Log the crash
        crash_message = (
            f"⚠️ **Bot Crash Detected**\n\n"
            f"**Error:** `{error_msg}`\n"
            f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Action:** Auto-restarting..."
        )
        
        await self.log_to_channel(bot, crash_message)
        
        # Schedule restart
        asyncio.create_task(self.restart_bot(bot))
    
    async def restart_bot(self, bot):
        """Restart the bot"""
        await self.notify_restart(bot, "Auto-restart after crash")
        
        # Wait a bit before restarting
        await asyncio.sleep(3)
        
        # Restart the process
        logger.info("Restarting bot process...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manual restart command for owner"""
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ Only the bot owner can use this command.")
            return
        
        await update.message.reply_text("🔄 Restarting bot...")
        await self.notify_restart(context.bot, "Manual restart by owner")
        
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def cmd_gban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global ban command for owner"""
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ Only the bot owner can use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "ℹ️ Reply to a user's message with /gban to globally ban them."
            )
            return
        
        target_user = update.message.reply_to_message.from_user
        
        if self.add_global_ban(target_user.id):
            await update.message.reply_text(
                f"✅ User {target_user.mention_html()} has been globally banned.\n"
                f"They will be blocked from using the bot everywhere.",
                parse_mode='HTML'
            )
            
            # Log to channel
            await self.log_to_channel(
                context.bot,
                f"🚫 **Global Ban Added**\n\n"
                f"**User:** {target_user.mention_html()}\n"
                f"**User ID:** `{target_user.id}`\n"
                f"**By:** {user.mention_html()}",
            )
        else:
            await update.message.reply_text(
                f"❌ User {target_user.mention_html()} is already globally banned.",
                parse_mode='HTML'
            )
    
    async def cmd_ungban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove global ban command for owner"""
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ Only the bot owner can use this command.")
            return
        
        # Check if replying to a message
        if not update.message.reply_to_message:
            await update.message.reply_text(
                "ℹ️ Reply to a user's message with /ungban to remove global ban."
            )
            return
        
        target_user = update.message.reply_to_message.from_user
        
        if self.remove_global_ban(target_user.id):
            await update.message.reply_text(
                f"✅ User {target_user.mention_html()} has been removed from global ban list.",
                parse_mode='HTML'
            )
            
            # Log to channel
            await self.log_to_channel(
                context.bot,
                f"✅ **Global Ban Removed**\n\n"
                f"**User:** {target_user.mention_html()}\n"
                f"**User ID:** `{target_user.id}`\n"
                f"**By:** {user.mention_html()}",
            )
        else:
            await update.message.reply_text(
                f"❌ User {target_user.mention_html()} is not globally banned.",
                parse_mode='HTML'
            )
    
    async def cmd_gbanlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show global ban list for owner"""
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ Only the bot owner can use this command.")
            return
        
        if not self.global_banned_users:
            await update.message.reply_text("📋 No users are currently globally banned.")
            return
        
        ban_list = "\n".join([f"• `{uid}`" for uid in sorted(self.global_banned_users)])
        message = (
            f"🚫 **Global Ban List**\n\n"
            f"**Total:** {len(self.global_banned_users)} users\n\n"
            f"{ban_list}"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot status for owner"""
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await update.message.reply_text("❌ Only the bot owner can use this command.")
            return
        
        uptime = ""
        if self.last_restart_time:
            delta = datetime.now() - self.last_restart_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{hours}h {minutes}m {seconds}s"
        
        status_message = (
            f"📊 **Bot Status**\n\n"
            f"**Restarts:** {self.restart_count}\n"
            f"**Uptime:** {uptime if uptime else 'Just started'}\n"
            f"**Global Bans:** {len(self.global_banned_users)}\n"
            f"**Last Restart:** {self.last_restart_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_restart_time else 'N/A'}"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    def get_handlers(self):
        """Return command handlers"""
        return [
            CommandHandler("restart", self.cmd_restart),
            CommandHandler("reload", self.cmd_restart),
            CommandHandler("gban", self.cmd_gban),
            CommandHandler("ungban", self.cmd_ungban),
            CommandHandler("gbanlist", self.cmd_gbanlist),
            CommandHandler("status", self.cmd_status),
        ]


# Global instance
maintenance_manager = MaintenanceManager()
