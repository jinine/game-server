from fastapi import FastAPI
from routes import player
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"message": "Healthy!"}

app.include_router(player.router)
