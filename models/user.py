from pydantic import BaseModel
from datetime import datetime


class User(BaseModel):
    email: str
    loginType: list[str] | list
    user_preferences: dict[str, str] | None
    created_at: datetime = datetime.now()
