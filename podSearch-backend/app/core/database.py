from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

database = Database()

async def connect_to_mongo():
    """Create database connection"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "podsearch")
    
    database.client = AsyncIOMotorClient(mongodb_url)
    database.database = database.client[database_name]
    
    from ..models.transcript_db import TranscriptSegmentDB
    
    await init_beanie(
        database=database.database,
        document_models=[TranscriptSegmentDB]
    )

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()

def get_database():
    """Get database instance"""
    return database.database 