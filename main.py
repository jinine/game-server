from fastapi import FastAPI
from routes import player

app = FastAPI()

@app.get("/")
def health():
    return {"message": "Healthy!"}

app.include_router(player.router)
