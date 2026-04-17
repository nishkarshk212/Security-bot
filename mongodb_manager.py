"""
MongoDB Manager - Handles freed members and permissions storage
"""
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

try:
    from pymongo import MongoClient, ASCENDING
    from pymongo.errors import ConnectionFailure, PyMongoError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("pymongo not installed. MongoDB features will be disabled.")

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', '')
DATABASE_NAME = 'SecurityBot'


class MongoDBManager:
    """Manages MongoDB connection and freed members data"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.freed_members = None
        self.connected = False
        
        if MONGODB_AVAILABLE and MONGODB_URI:
            self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            if not MONGODB_AVAILABLE:
                logger.warning("MongoDB disabled: pymongo not installed")
                return False
            
            if not MONGODB_URI:
                logger.warning("MongoDB disabled: MONGODB_URI not configured")
                return False
            
            logger.info("🔗 Connecting to MongoDB...")
            self.client = MongoClient(MONGODB_URI)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Select database and collection
            self.db = self.client[DATABASE_NAME]
            self.freed_members = self.db['freed_members']
            
            # Create indexes for faster queries
            self.freed_members.create_index([
                ("chat_id", ASCENDING),
                ("user_id", ASCENDING)
            ], unique=True)
            
            self.freed_members.create_index([("chat_id", ASCENDING)])
            self.freed_members.create_index([("user_id", ASCENDING)])
            self.freed_members.create_index([("approved_at", ASCENDING)])
            
            self.connected = True
            logger.info("✅ Connected to MongoDB successfully")
            logger.info(f"📊 Database: {DATABASE_NAME}")
            logger.info(f"📁 Collection: freed_members")
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
        except PyMongoError as e:
            logger.error(f"❌ MongoDB error: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            self.connected = False
            return False
    
    async def add_freed_member(self, chat_id, user_id, username, first_name, approved_by, exemptions=None):
        """Add or update a freed member in MongoDB"""
        if not self.connected:
            return False
        
        try:
            if exemptions is None:
                exemptions = {
                    'exempt_stickers': True,
                    'exempt_media': True,
                    'exempt_forwards': False,
                    'exempt_commands': False,
                    'exempt_premium_stickers': True,
                    'exempt_channel_posts': False,
                    'exempt_pinned_messages': False,
                    'exempt_contacts': True,
                    'exempt_location': True,
                    'exempt_documents': True,
                    'exempt_voice': True,
                    'exempt_video_note': True,
                    'exempt_poll': True,
                    'exempt_embed_link': True,
                    'exempt_links': False
                }
            
            member_data = {
                'chat_id': chat_id,
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'approved_by': approved_by,
                'exemptions': exemptions,
                'approved_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Upsert: insert or update
            result = await asyncio.to_thread(
                self.freed_members.update_one,
                {'chat_id': chat_id, 'user_id': user_id},
                {'$set': member_data},
                upsert=True
            )
            
            logger.info(f"✅ Freed member saved to MongoDB: {user_id} in {chat_id}")
            return True
            
        except PyMongoError as e:
            logger.error(f"❌ Error adding freed member to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    async def get_freed_member(self, chat_id, user_id):
        """Get a freed member's data"""
        if not self.connected:
            return None
        
        try:
            member = await asyncio.to_thread(
                self.freed_members.find_one,
                {'chat_id': chat_id, 'user_id': user_id}
            )
            
            return member
            
        except PyMongoError as e:
            logger.error(f"❌ Error getting freed member from MongoDB: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    async def update_exemptions(self, chat_id, user_id, exemptions):
        """Update a freed member's exemptions"""
        if not self.connected:
            return False
        
        try:
            result = await asyncio.to_thread(
                self.freed_members.update_one,
                {'chat_id': chat_id, 'user_id': user_id},
                {
                    '$set': {
                        'exemptions': exemptions,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Exemptions updated in MongoDB: {user_id} in {chat_id}")
                return True
            else:
                logger.warning(f"⚠️ No member found to update: {user_id} in {chat_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ Error updating exemptions in MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    async def remove_freed_member(self, chat_id, user_id):
        """Remove a freed member from MongoDB"""
        if not self.connected:
            return False
        
        try:
            result = await asyncio.to_thread(
                self.freed_members.delete_one,
                {'chat_id': chat_id, 'user_id': user_id}
            )
            
            if result.deleted_count > 0:
                logger.info(f"✅ Freed member removed from MongoDB: {user_id} in {chat_id}")
                return True
            else:
                logger.warning(f"⚠️ No member found to remove: {user_id} in {chat_id}")
                return False
                
        except PyMongoError as e:
            logger.error(f"❌ Error removing freed member from MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    async def get_all_freed_members(self, chat_id):
        """Get all freed members for a specific chat"""
        if not self.connected:
            return []
        
        try:
            cursor = await asyncio.to_thread(
                lambda: list(self.freed_members.find({'chat_id': chat_id}).sort('approved_at', -1))
            )
            return cursor
            
        except PyMongoError as e:
            logger.error(f"❌ Error getting freed members from MongoDB: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return []
    
    async def get_freed_members_count(self, chat_id):
        """Get count of freed members for a chat"""
        if not self.connected:
            return 0
        
        try:
            count = await asyncio.to_thread(
                self.freed_members.count_documents,
                {'chat_id': chat_id}
            )
            return count
            
        except PyMongoError as e:
            logger.error(f"❌ Error counting freed members in MongoDB: {e}")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return 0
    
    async def remove_all_freed_members(self, chat_id):
        """Remove all freed members for a chat (unfreeall)"""
        if not self.connected:
            return 0
        
        try:
            result = await asyncio.to_thread(
                self.freed_members.delete_many,
                {'chat_id': chat_id}
            )
            deleted_count = result.deleted_count
            
            logger.info(f"✅ Removed {deleted_count} freed members from MongoDB: {chat_id}")
            return deleted_count
            
        except PyMongoError as e:
            logger.error(f"❌ Error removing all freed members from MongoDB: {e}")
            return 0
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return 0
    
    async def is_user_freed(self, chat_id, user_id):
        """Check if a user is freed in a chat"""
        if not self.connected:
            return False
        
        try:
            count = await asyncio.to_thread(
                self.freed_members.count_documents,
                {'chat_id': chat_id, 'user_id': user_id}
            )
            return count > 0
            
        except PyMongoError as e:
            logger.error(f"❌ Error checking if user is freed in MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    async def get_user_exemptions(self, chat_id, user_id):
        """Get user's exemptions"""
        if not self.connected:
            return None
        
        try:
            member = await asyncio.to_thread(
                self.freed_members.find_one,
                {'chat_id': chat_id, 'user_id': user_id}
            )
            
            if member:
                return member.get('exemptions', {})
            return None
            
        except PyMongoError as e:
            logger.error(f"❌ Error getting exemptions from MongoDB: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    async def migrate_from_sqlite(self, sqlite_db_manager):
        """Migrate data from SQLite to MongoDB"""
        if not self.connected:
            return False
        
        try:
            logger.info("🔄 Starting migration from SQLite to MongoDB...")
            
            # Get all approved users from SQLite
            import aiosqlite
            async with aiosqlite.connect(sqlite_db_manager.db_file) as db:
                cursor = await db.execute(
                    'SELECT chat_id, user_id, username, first_name, approved_by, '
                    'exempt_stickers, exempt_media, exempt_forwards, exempt_commands, '
                    'exempt_premium_stickers, exempt_channel_posts, exempt_pinned_messages, '
                    'exempt_contacts, exempt_location, exempt_documents, exempt_voice, '
                    'exempt_video_note, exempt_poll, exempt_embed_link, exempt_links '
                    'FROM approved_users'
                )
                rows = await cursor.fetchall()
            
            migrated_count = 0
            for row in rows:
                chat_id, user_id, username, first_name, approved_by = row[:5]
                exemptions = {
                    'exempt_stickers': bool(row[5]),
                    'exempt_media': bool(row[6]),
                    'exempt_forwards': bool(row[7]),
                    'exempt_commands': bool(row[8]),
                    'exempt_premium_stickers': bool(row[9]),
                    'exempt_channel_posts': bool(row[10]),
                    'exempt_pinned_messages': bool(row[11]),
                    'exempt_contacts': bool(row[12]),
                    'exempt_location': bool(row[13]),
                    'exempt_documents': bool(row[14]),
                    'exempt_voice': bool(row[15]),
                    'exempt_video_note': bool(row[16]),
                    'exempt_poll': bool(row[17]),
                    'exempt_embed_link': bool(row[18]),
                    'exempt_links': bool(row[19]) if len(row) > 19 else False
                }
                
                success = await self.add_freed_member(
                    chat_id, user_id, username, first_name, approved_by, exemptions
                )
                if success:
                    migrated_count += 1
            
            logger.info(f"✅ Migration complete: {migrated_count}/{len(rows)} members migrated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            return False
    
    def get_stats(self):
        """Get MongoDB statistics"""
        if not self.connected:
            return {"connected": False}
        
        try:
            total_members = self.freed_members.count_documents({})
            total_chats = len(self.freed_members.distinct('chat_id'))
            
            return {
                "connected": True,
                "total_freed_members": total_members,
                "total_chats": total_chats,
                "database": DATABASE_NAME,
                "collection": "freed_members"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }


# Global instance
mongodb_manager = MongoDBManager()
