from pydantic import BaseModel
from datetime import datetime


class UserBehavior(BaseModel):
    user_id: str
    user_email: str
    seen_news: list[str] | list
    preference: dict[str, int]
    created_at: datetime = datetime.now()
