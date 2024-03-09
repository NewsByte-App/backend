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
from transformers import pipeline, BartTokenizer


from utils.news_fetcher import fetch_news

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
    if existingUser and set(user.loginType).issubset(set(existingUser["loginType"])):
        return JSONResponse(status_code=400, content={"message": "User already exists"})
    elif existingUser and not set(user.loginType).issubset(set(existingUser["loginType"])):
        loginTypes = list(set(existingUser["loginType"] + user.loginType))
        existingUser["loginType"] = loginTypes
        updated_user = user_collection.update(
            {"_id": existingUser["_id"]}, existingUser)
        if updated_user:
            serialized_user = json.dumps(
                dict(user), indent=4, sort_keys=True, default=str)
            return JSONResponse(content=json.loads(serialized_user), status_code=200)

        return JSONResponse(status_code=400, content={"message": "Error Updating User"})
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
# @repeat_every(seconds=43200)
# async def curate_news():
#     try:
#         res = fetch_news()
#         for data in res:
#             existing_news_item = news_collection.find_one(
#                 {"title": data["title"]})
#             if existing_news_item is None and data['url'] is not None:
#                 content = google_news.get_full_article(data['url'])
#                 if content is not None and data['author'] is not None:
#                     news_item = News(
#                         title=data["title"],
#                         description=data["description"] if data.get(
#                             "description") else "",
#                         published_date=datetime.fromisoformat(
#                             data['publishedAt'].rstrip('Z')),
#                         url=data["url"],
#                         category=data['category'],
#                         summary="",
#                         content=content.text,
#                         image_url=list(content.images)[0],
#                         summarized=False,
#                         author=data["description"] if data.get(
#                             "description") else "",
#                     )
#                     news_collection.insert_one(dict(news_item))
#     except Exception as e:
#         print(e)


@router.on_event('startup')
# Consider adjusting the frequency based on your needs
@repeat_every(seconds=50)
async def summarize():
    try:
        # Fetch news articles that haven't been summarized yet
        news = news_collection.find({'summarized': False})

        for data in news:
            summary = summarizer(
                data['content'].strip(), max_length=120, truncation=True)
            data['summary'] = summary[0]['summary_text']
            data['summarized'] = True
            print(data)
            updated_news = news_collection.update({'_id': data['_id']}, data)
            print(updated_news)
            print("Done")
    except Exception as e:
        print(e)
