from pydantic import BaseModel
from datetime import datetime


class News(BaseModel):
    title: str
    content: str
    description: str
    summary: str
    url: str
    image_url: str
    published_date: datetime
    created_at: datetime = datetime.now()
    summarized: bool = False
