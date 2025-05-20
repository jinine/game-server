from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from database import db
from models import Player, Token
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_player,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta

router = APIRouter()

@router.post("/players/")
async def create_player(player: Player):
    if await db.players.find_one({"username": player.username}):
        raise HTTPException(status_code=400, detail="Player already exists")
    
    # Hash the password before storing
    player_dict = player.dict()
    player_dict["password"] = get_password_hash(player_dict["password"])
    
    result = await db.players.insert_one(player_dict)
    return {"id": str(result.inserted_id)}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    player = await db.players.find_one({"username": form_data.username})
    if not player or not verify_password(form_data.password, player["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": player["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/players/me")
async def read_players_me(current_player: Player = Depends(get_current_player)):
    return current_player

@router.get("/players/{username}")
async def get_player(username: str):
    player = await db.players.find_one({"username": username})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player["_id"] = str(player["_id"])
    return player
