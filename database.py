from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URL=os.getenv('MONGO_URL')

client = AsyncIOMotorClient(MONGO_URL)

db = client["game_server"]

async def get_database():
    """
    Get the database instance.
    This function is used to provide database access to other parts of the application.
    """
    return db
