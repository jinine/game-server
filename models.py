from pydantic import BaseModel
from typing import List, Optional

class Player(BaseModel):
    username: str
    password: str
    email: Optional[str]
    main_highest_score: int = 0
    main_highest_combo: int = 0
    created_at: str

