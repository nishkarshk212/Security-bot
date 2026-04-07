"""
Media message blocking module.
Handles deletion of photos, videos, documents, audio, voice, and video notes.
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def delete_after(message, seconds):
    """Delete a message after specified seconds."""
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete warning message: {e}")


async def block_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Block media messages based on group settings."""
    if not update.effective_chat or update.effective_chat.type not in ["group", "supergroup"]:
        return
    
    chat_id = update.effective_chat.id
    message = update.effective_message
    
    if not message:
        return
    
    # Check if message contains media
    has_media = (
        message.photo or 
        message.video or 
        message.document or 
        message.audio or 
        message.voice or 
        message.video_note
    )
    
    if not has_media:
        return
    
    # Get settings from the update context
    settings = context.bot_data.get('group_settings', {}).get(chat_id, {})
    
    # Check if media blocking is enabled
    if not settings.get('block_media', True):
        return
    
    # Check if user is admin - admins are exempt
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status in ["administrator", "creator"]:
                return  # Don't block admins
        except Exception as e:
            logger.error(f"Failed to check user status: {e}")
        
        # Check if user is exempt
        exempt_users = settings.get('exempt_users', [])
        if user_id in exempt_users:
            # Check for user-specific settings
            user_specific = settings.get('user_specific_settings', {}).get(str(user_id))
            if user_specific and not user_specific.get('block_media', True):
                return  # User has media allowed
            elif not user_specific:
                return  # Fully exempt user
    
    # Delete the media message
    try:
        await message.delete()
        user = message.from_user
        if user:
            username = f"@{user.username}" if user.username else user.first_name
            warning = await message.reply_text(
                f"⚠️ {username}\\n"
                f"Media messages are not allowed\\.\\n\\n"
                f"Please review the group settings\\.",
                parse_mode="MarkdownV2"
            )
            logger.info(f"Media message deleted in {chat_id} | User {user.id}")
            
            # Delete warning after 10 seconds
            asyncio.create_task(delete_after(warning, 10))
    except Exception as e:
        logger.error(f"Failed to delete media message: {e}")
