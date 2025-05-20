from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from datetime import datetime
from utils.match_helper import MatchmakingQueue
from database import get_database

router = APIRouter(
    prefix="/matchmaking",
    tags=["matchmaking"],
    responses={404: {"description": "Not found"}},
)

# Initialize matchmaking queue
matchmaking = None

@router.on_event("startup")
async def startup_event():
    global matchmaking
    db = await get_database()
    matchmaking = MatchmakingQueue(db)

@router.post("/queue")
async def join_queue(player_id: str, score: int) -> Dict:
    """
    Join the matchmaking queue.
    
    Args:
        player_id: The ID of the player joining the queue
        score: The player's current score
        
    Returns:
        Dict containing queue status and match information if found
    """
    if not await matchmaking.validate_queue_entry(player_id, score):
        raise HTTPException(status_code=400, detail="Invalid queue entry")
    
    if await matchmaking.add_to_queue(player_id, score):
        opponent = await matchmaking.find_match(player_id, score)
        if opponent:
            match_id = await matchmaking.create_match(player_id, opponent)
            return {
                "status": "matched",
                "match_id": match_id,
                "opponent_id": opponent,
                "timestamp": datetime.utcnow()
            }
        return {
            "status": "queued",
            "position": await matchmaking.get_queue_position(player_id),
            "timestamp": datetime.utcnow()
        }
    raise HTTPException(status_code=500, detail="Failed to join queue")

@router.delete("/queue/{player_id}")
async def leave_queue(player_id: str) -> Dict:
    """
    Leave the matchmaking queue.
    
    Args:
        player_id: The ID of the player leaving the queue
        
    Returns:
        Dict containing the status of the operation
    """
    if await matchmaking.remove_from_queue(player_id):
        return {
            "status": "success",
            "message": "Successfully left queue",
            "timestamp": datetime.utcnow()
        }
    raise HTTPException(status_code=404, detail="Player not found in queue")

@router.get("/queue/status/{player_id}")
async def get_queue_status(player_id: str) -> Dict:
    """
    Get the current status of a player in the queue.
    
    Args:
        player_id: The ID of the player to check
        
    Returns:
        Dict containing queue status information
    """
    position = await matchmaking.get_queue_position(player_id)
    if position == -1:
        raise HTTPException(status_code=404, detail="Player not found in queue")
    
    return {
        "player_id": player_id,
        "position": position,
        "queue_size": await matchmaking.get_queue_size(),
        "timestamp": datetime.utcnow()
    }

@router.get("/queue/stats")
async def get_queue_stats() -> Dict:
    """
    Get overall queue statistics.
    
    Returns:
        Dict containing queue statistics
    """
    return await matchmaking.get_queue_status()

@router.get("/match/{match_id}")
async def get_match_info(match_id: str) -> Dict:
    """
    Get information about a specific match.
    
    Args:
        match_id: The ID of the match to retrieve
        
    Returns:
        Dict containing match information
    """
    match_info = await matchmaking.get_match_details(match_id)
    if not match_info:
        raise HTTPException(status_code=404, detail="Match not found")
    return match_info

@router.post("/match/{match_id}/cancel")
async def cancel_match(match_id: str, player_id: str) -> Dict:
    """
    Cancel an active match.
    
    Args:
        match_id: The ID of the match to cancel
        player_id: The ID of the player requesting the cancellation
        
    Returns:
        Dict containing the status of the operation
    """
    match_info = await matchmaking.get_match_details(match_id)
    if not match_info:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if player_id not in [match_info["player1_id"], match_info["player2_id"]]:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this match")
    
    # Update match status
    await matchmaking.matches_collection.update_one(
        {"_id": match_id},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
    )
    
    return {
        "status": "success",
        "message": "Match cancelled successfully",
        "timestamp": datetime.utcnow()
    }

@router.get("/queue/cleanup")
async def cleanup_queue() -> Dict:
    """
    Clean up stale queue entries.
    This endpoint should be called periodically by a maintenance task.
    
    Returns:
        Dict containing cleanup statistics
    """
    cleaned_count = await matchmaking.clean_stale_queue_entries()
    return {
        "status": "success",
        "cleaned_entries": cleaned_count,
        "timestamp": datetime.utcnow()
    }
