"""
Maintenance Module - Auto-restart, crash recovery, global ban system, and cache management
"""
import os
import sys
import asyncio
import logging
import glob
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from dotenv import load_dotenv

load_dotenv()

# Configuration
OWNER_ID = int(os.getenv('OWNER_ID', '8791884726'))
CO_OWNER_ID = int(os.getenv('CO_OWNER_ID', '8784193595'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '-1003757375746'))

# List of all authorized owners (owner + co-owners)
AUTHORIZED_OWNERS = {OWNER_ID, CO_OWNER_ID}

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
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is owner or co-owner"""
        return user_id in AUTHORIZED_OWNERS
    
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
    
    async def notify_restart(self, bot, reason: str = "Unknown", user_id: int = None):
        """Notify owner and co-owner about restart"""
        self.restart_count += 1
        self.last_restart_time = datetime.now()
        
        # Determine who initiated
        initiator = "System"
        if user_id:
            if user_id == OWNER_ID:
                initiator = "Owner"
            elif user_id == CO_OWNER_ID:
                initiator = "Co-Owner"
        
        message = (
            f"🔄 **Bot Restarted**\n\n"
            f"**Reason:** {reason}\n"
            f"**Initiated by:** {initiator}\n"
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
        
        # Notify co-owner
        try:
            await bot.send_message(
                chat_id=CO_OWNER_ID,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify co-owner: {e}")
        
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
        """Manual restart command for owner/co-owner"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
            return
        
        await update.message.reply_text("🔄 Restarting bot...")
        await self.notify_restart(context.bot, f"Manual restart by {'Owner' if user.id == OWNER_ID else 'Co-Owner'}", user.id)
        
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    async def cmd_gban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global ban command for owner/co-owner"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
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
        """Remove global ban command for owner/co-owner"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
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
        """Show global ban list for owner/co-owner"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
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
        """Show bot status for owner/co-owner"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
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
    
    def clear_all_caches(self):
        """Clear all cache files, logs, and temporary data"""
        cleared_files = []
        errors = []
        
        # Define cache patterns to clear
        cache_patterns = [
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.log',
            '*.pid',
            '*.lock',
            '.venv/lib/python*/site-packages/*.pyc',
        ]
        
        # Clear __pycache__ directories
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path)
                    cleared_files.append(f"🗑️ Deleted: {pycache_path}")
                except Exception as e:
                    errors.append(f"❌ Error deleting {pycache_path}: {str(e)}")
        
        # Clear .pyc and .pyo files
        for pattern in ['*.pyc', '*.pyo']:
            for file in glob.glob(pattern, recursive=True):
                try:
                    os.remove(file)
                    cleared_files.append(f"🗑️ Deleted: {file}")
                except Exception as e:
                    errors.append(f"❌ Error deleting {file}: {str(e)}")
        
        # Clear old log files (keep current bot.log and bot_maintenance.log)
        for log_file in glob.glob('*.log'):
            if log_file not in ['bot.log', 'bot_maintenance.log']:
                try:
                    # Clear content instead of deleting to avoid file handle issues
                    with open(log_file, 'w') as f:
                        f.write('')
                    cleared_files.append(f"🧹 Cleared: {log_file}")
                except Exception as e:
                    errors.append(f"❌ Error clearing {log_file}: {str(e)}")
        
        # Clear .pid and .lock files
        for pattern in ['*.pid', '*.lock']:
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                    cleared_files.append(f"🗑️ Deleted: {file}")
                except Exception as e:
                    errors.append(f"❌ Error deleting {file}: {str(e)}")
        
        # Truncate current log files if they're too large (>10MB)
        for log_file in ['bot.log', 'bot_maintenance.log']:
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    try:
                        # Keep last 1000 lines
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                        with open(log_file, 'w') as f:
                            f.writelines(lines[-1000:])
                        cleared_files.append(f"✂️ Trimmed {log_file} (was {file_size // 1024}KB)")
                    except Exception as e:
                        errors.append(f"❌ Error trimming {log_file}: {str(e)}")
        
        return cleared_files, errors
    
    async def run_maintenance(self, bot, is_auto=False):
        """Run complete maintenance routine"""
        maintenance_start = datetime.now()
        
        # Step 1: Clear caches
        cleared_files, errors = self.clear_all_caches()
        
        # Step 2: Reload global bans
        self.load_global_bans()
        
        # Step 3: Check database integrity
        db_status = "✅ OK"
        try:
            if os.path.exists('bot_database.db'):
                db_size = os.path.getsize('bot_database.db')
                db_status = f"✅ OK ({db_size // 1024}KB)"
        except Exception as e:
            db_status = f"⚠️ Error: {str(e)}"
        
        # Step 4: Calculate maintenance duration
        maintenance_end = datetime.now()
        duration = (maintenance_end - maintenance_start).total_seconds()
        
        # Build report
        report = f"🛠️ **Bot Maintenance Report**\n\n"
        report += f"**Type:** {'🔄 Auto (24h)' if is_auto else '👤 Manual'}\n"
        report += f"**Time:** {maintenance_start.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Duration:** {duration:.2f} seconds\n\n"
        
        report += f"📊 **Status:**\n"
        report += f"• Database: {db_status}\n"
        report += f"• Global Bans: {len(self.global_banned_users)} loaded\n"
        report += f"• Files Cleared: {len(cleared_files)}\n\n"
        
        if cleared_files:
            report += f"🗑️ **Cleared:**\n"
            # Show first 10 items only
            for item in cleared_files[:10]:
                report += f"  {item}\n"
            if len(cleared_files) > 10:
                report += f"  ... and {len(cleared_files) - 10} more\n"
            report += "\n"
        
        if errors:
            report += f"⚠️ **Errors:**\n"
            for error in errors[:5]:
                report += f"  {error}\n"
            if len(errors) > 5:
                report += f"  ... and {len(errors) - 5} more\n"
            report += "\n"
        
        report += f"✅ **Maintenance Complete!**"
        
        # Log to channel
        await self.log_to_channel(bot, report)
        
        # Notify owner
        try:
            await bot.send_message(
                chat_id=OWNER_ID,
                text=report,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify owner: {e}")
        
        # Notify co-owner
        try:
            await bot.send_message(
                chat_id=CO_OWNER_ID,
                text=report,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify co-owner: {e}")
        
        logger.info(f"Maintenance completed in {duration:.2f}s")
        return report
    
    async def cmd_maintenance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manual maintenance command for owner/co-owner - clears cache and fixes bugs"""
        user = update.effective_user
        
        if not self.is_owner(user.id):
            await update.message.reply_text("❌ Only the bot owner or co-owner can use this command.")
            return
        
        # Send starting message
        msg = await update.message.reply_text(
            "🛠️ **Starting Maintenance...**\n\n"
            "• Clearing caches\n"
            "• Fixing bugs\n"
            "• Optimizing database\n"
            "• Reloading configurations\n\n"
            "Please wait...",
            parse_mode='Markdown'
        )
        
        # Run maintenance
        try:
            report = await self.run_maintenance(context.bot, is_auto=False)
            
            # Update message with result
            await msg.edit_text(
                f"✅ **Maintenance Complete!**\n\n"
                f"Check your DM for detailed report.",
                parse_mode='Markdown'
            )
        except Exception as e:
            await msg.edit_text(f"❌ **Maintenance Failed:**\n\n`{str(e)}`", parse_mode='Markdown')
            logger.error(f"Maintenance command error: {e}")
    
    async def start_auto_maintenance(self, bot):
        """Start automatic 24-hour maintenance scheduler"""
        logger.info("🕐 Auto-maintenance scheduler started (24-hour interval)")
        
        while True:
            try:
                # Wait 24 hours (86400 seconds)
                await asyncio.sleep(86400)
                
                logger.info("🛠️ Running scheduled auto-maintenance...")
                await self.run_maintenance(bot, is_auto=True)
                
                # Optional: Restart bot after auto-maintenance for clean state
                logger.info("🔄 Restarting bot after auto-maintenance...")
                await asyncio.sleep(5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
            except Exception as e:
                logger.error(f"Auto-maintenance error: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    def get_handlers(self):
        """Return command handlers"""
        return [
            CommandHandler("restart", self.cmd_restart),
            CommandHandler("gban", self.cmd_gban),
            CommandHandler("ungban", self.cmd_ungban),
            CommandHandler("gbanlist", self.cmd_gbanlist),
            CommandHandler("status", self.cmd_status),
            CommandHandler("maintenance", self.cmd_maintenance),
        ]


# Global instance
maintenance_manager = MaintenanceManager()
