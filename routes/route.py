from datetime import datetime
import json
from fastapi_utilities import repeat_every
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import requests
from models.news import News
from config.database import news_collection, user_collection
from models.user import User
from schema.schemas import list_serial_news, list_serial_users, individual_serial_users
from bson import ObjectId
from gnews import GNews
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


router = APIRouter()

google_news = GNews(language='en', country='US', period='1d')


@router.get("/")
async def get_news():
    news = list_serial_news(news_collection.find())
    return news


@router.post("/")
async def post_news(news: News):
    news_collection.insert_one(dict(news))


@router.get("/get-user/{email_id}")
async def get_user(email_id: str):
    response = user_collection.find_one({'email': email_id})
    if response:
        user = individual_serial_users(response)
        return JSONResponse(content=user, status_code=200)
    return JSONResponse(status_code=400, content={"message": "No User Found"})


@router.post("/create-user")
async def create_user(user: User):
    existingUser = user_collection.find_one({'email': user.email})
    if existingUser:
        return JSONResponse(status_code=400, content={"message": "User already exists"})
    else:
        # Serialize datetime objects using a custom function
        serialized_user = json.dumps(
            dict(user), indent=4, sort_keys=True, default=str)

        inserted_user = user_collection.insert_one(
            json.loads(serialized_user)).inserted_id

        if inserted_user:
            return JSONResponse(content=json.loads(serialized_user), status_code=200)

        return JSONResponse(status_code=400, content={"message": "Couldn't create user"})


# @router.on_event('startup')
# @repeat_every(seconds=20)
# async def curate_news():
#     try:
#         res = google_news.get_news("US")
#         for data in res:
#             existing_news_item = news_collection.find_one(
#                 {"title": data["title"]})
#             if existing_news_item is None:
#                 content = google_news.get_full_article(data['url'])
#                 if content is not None:
#                     news_item = News(
#                         title=data["title"],
#                         description=data["description"],
#                         published_date=datetime.strptime(
#                             data["published date"], '%a, %d %b %Y %H:%M:%S GMT'
#                         ),
#                         url=data["url"],
#                         summary=summarizer(content.text, max_length=60,
#                                            min_length=30, do_sample=False)[0]['summary_text'],
#                         content=content.text,
#                         image_url=content.images[0],
#                         summarized=False
#                     )
#                     news_collection.insert_one(dict(news_item))
#     except Exception as e:
#         print(e)
