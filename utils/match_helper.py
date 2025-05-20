from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_SCORE_DIFFERENCE = 100  # Maximum score difference for initial matching
QUEUE_TIMEOUT_MINUTES = 5   # Time before expanding matchmaking criteria
EXPANDED_SCORE_DIFFERENCE = 200  # Score difference after timeout

class MatchmakingQueue:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client
        self.queue_collection = self.db.queue
        self.matches_collection = self.db.matches

    async def add_to_queue(self, player_id: str, score: int) -> bool:
        """Add a player to the matchmaking queue."""
        try:
            queue_entry = {
                "player_id": player_id,
                "score": score,
                "joined_at": datetime.utcnow(),
                "status": "waiting"
            }
            await self.queue_collection.update_one(
                {"player_id": player_id},
                {"$set": queue_entry},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding player to queue: {e}")
            return False

    async def remove_from_queue(self, player_id: str) -> bool:
        """Remove a player from the matchmaking queue."""
        try:
            result = await self.queue_collection.delete_one({"player_id": player_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error removing player from queue: {e}")
            return False

    async def get_queue_position(self, player_id: str) -> int:
        """Get player's position in the queue."""
        try:
            player = await self.queue_collection.find_one({"player_id": player_id})
            if not player:
                return -1
            
            # Count players who joined before this player
            position = await self.queue_collection.count_documents({
                "joined_at": {"$lt": player["joined_at"]}
            })
            return position + 1
        except Exception as e:
            logger.error(f"Error getting queue position: {e}")
            return -1

    async def find_match(self, player_id: str, score: int) -> Optional[str]:
        """Find a suitable opponent for the player."""
        try:
            # First try to find a match within the initial score difference
            match = await self.queue_collection.find_one({
                "player_id": {"$ne": player_id},
                "status": "waiting",
                "score": {
                    "$gte": score - MAX_SCORE_DIFFERENCE,
                    "$lte": score + MAX_SCORE_DIFFERENCE
                }
            })

            if not match:
                # If no match found, try with expanded criteria
                match = await self.queue_collection.find_one({
                    "player_id": {"$ne": player_id},
                    "status": "waiting",
                    "score": {
                        "$gte": score - EXPANDED_SCORE_DIFFERENCE,
                        "$lte": score + EXPANDED_SCORE_DIFFERENCE
                    }
                })

            return match["player_id"] if match else None
        except Exception as e:
            logger.error(f"Error finding match: {e}")
            return None

    def calculate_score_difference(self, player1_score: int, player2_score: int) -> int:
        """Calculate the absolute difference between two players' scores."""
        return abs(player1_score - player2_score)

    def is_valid_match(self, player1_score: int, player2_score: int, max_difference: int) -> bool:
        """Check if two players are within acceptable score range."""
        return self.calculate_score_difference(player1_score, player2_score) <= max_difference

    async def get_queue_size(self) -> int:
        """Get current number of players in queue."""
        try:
            return await self.queue_collection.count_documents({"status": "waiting"})
        except Exception as e:
            logger.error(f"Error getting queue size: {e}")
            return 0

    async def get_queue_status(self) -> Dict:
        """Get detailed queue status."""
        try:
            total = await self.get_queue_size()
            avg_score = await self.queue_collection.aggregate([
                {"$match": {"status": "waiting"}},
                {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
            ]).to_list(1)
            
            return {
                "total_players": total,
                "average_score": avg_score[0]["avg_score"] if avg_score else 0,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {"total_players": 0, "average_score": 0, "timestamp": datetime.utcnow()}

    async def is_player_in_queue(self, player_id: str) -> bool:
        """Check if player is currently in queue."""
        try:
            result = await self.queue_collection.find_one({"player_id": player_id})
            return result is not None
        except Exception as e:
            logger.error(f"Error checking queue status: {e}")
            return False

    async def create_match(self, player1_id: str, player2_id: str) -> str:
        """Create a new match between two players."""
        try:
            match_id = str(ObjectId())
            match_data = {
                "_id": match_id,
                "player1_id": player1_id,
                "player2_id": player2_id,
                "created_at": datetime.utcnow(),
                "status": "active"
            }
            await self.matches_collection.insert_one(match_data)
            
            # Remove both players from queue
            await self.remove_from_queue(player1_id)
            await self.remove_from_queue(player2_id)
            
            return match_id
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return None

    async def get_match_details(self, match_id: str) -> Dict:
        """Get details of a specific match."""
        try:
            match = await self.matches_collection.find_one({"_id": match_id})
            return match if match else {}
        except Exception as e:
            logger.error(f"Error getting match details: {e}")
            return {}

    async def clean_stale_queue_entries(self) -> int:
        """Remove players who have been in queue too long."""
        try:
            timeout_threshold = datetime.utcnow() - timedelta(minutes=QUEUE_TIMEOUT_MINUTES)
            result = await self.queue_collection.delete_many({
                "joined_at": {"$lt": timeout_threshold}
            })
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning stale entries: {e}")
            return 0

    async def handle_queue_error(self, player_id: str, error_type: str) -> None:
        """Handle various queue-related errors."""
        try:
            error_log = {
                "player_id": player_id,
                "error_type": error_type,
                "timestamp": datetime.utcnow()
            }
            await self.db.queue_errors.insert_one(error_log)
            logger.error(f"Queue error for player {player_id}: {error_type}")
        except Exception as e:
            logger.error(f"Error handling queue error: {e}")

    async def validate_queue_entry(self, player_id: str, score: int) -> bool:
        """Validate player data before adding to queue."""
        try:
            # Check if player is already in queue
            if await self.is_player_in_queue(player_id):
                return False
            
            # Validate score is positive
            if score < 0:
                return False
            
            # Add any other validation rules here
            
            return True
        except Exception as e:
            logger.error(f"Error validating queue entry: {e}")
            return False
