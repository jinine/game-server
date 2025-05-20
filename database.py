from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL="mongodb+srv://jinine:HevAz34ivQfkgJ8P@gameserver.t3k9ki3.mongodb.net/?retryWrites=true&w=majority&appName=gameServer"

client = AsyncIOMotorClient(MONGO_URL)

db = client["game_server"]
