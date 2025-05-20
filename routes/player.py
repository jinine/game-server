from fastapi import APIRouter, HTTPException
from database import db
from models import Player

router = APIRouter()

@router.post("/players/")
async def create_player(player: Player):
    if await db.players.find_one({"username": player.username}):
        raise HTTPException(status_code=400, detail="Player already exists")
    result = await db.players.insert_one(player.dict())
    return {"id": str(result.inserted_id)}

@router.get("/players/{username}")
async def get_player(username: str):
    player = await db.players.find_one({"username": username})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player["_id"] = str(player["_id"])
    return player
