from datetime import datetime
import json
from fastapi_utilities import repeat_every
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from config.database import news_collection, user_collection, user_behavior_collection
from models.user import User
import pymongo
from bson import ObjectId
from models.user_behavior import UserBehavior
from schema.schemas import list_serial_news, individual_serial_users
from bson import ObjectId


from utils.functions import duration_str_to_seconds, normalize_preferences

router = APIRouter()


@router.get("/")
async def get_news():
    news = list_serial_news(news_collection.find())
    return news


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
        serialized_user = json.dumps(
            dict(user), indent=4, sort_keys=True, default=str)

        inserted_user = user_collection.insert_one(
            json.loads(serialized_user)).inserted_id

        if inserted_user:
            user_behavior_collection.insert_one(dict(user_id=str(inserted_user), user_email=json.loads(serialized_user)['email'], seen_news=[], preference={
                "general": 0,
                "business": 0,
                "sports": 0,
                "technology": 0,
                "entertainment": 0,
                "health": 0,
                "science": 0,
            }))
            return JSONResponse(content=json.loads(serialized_user), status_code=200)

        return JSONResponse(status_code=400, content={"message": "Couldn't create user"})


@router.get('/get_news')
async def get_news(page: int = 1, limit: int = 10, category: str = None):
    query = {'summarized': True}
    if category:
        query['category'] = category

    news_cursor = news_collection.find(query).skip(
        (page - 1) * limit).limit(limit).sort("published_date", pymongo.DESCENDING)
    news = list_serial_news(news_cursor)
    return news


@router.get('/recommend_news/{user_email}')
async def recommend_news(user_email: str):
    user_behavior = user_behavior_collection.find_one(
        {'user_email': user_email})
    if not user_behavior:
        raise HTTPException(status_code=404, detail="User behavior not found")

    preferences = {category: weight for category,
                   weight in user_behavior['preference'].items()}

    sorted_categories = sorted(preferences.items(), key=lambda item: -item[1])
    excluded_object_ids = [ObjectId(id) for id in user_behavior['seen_news']]
    recommended_news = []
    allocated_items = 0

    for category, _ in sorted_categories:
        news_item = news_collection.find_one(
            {'category': category, '_id': {'$nin': excluded_object_ids}})
        if news_item and news_item not in recommended_news:
            recommended_news.append(news_item)
            allocated_items += 1

    remaining_slots = 10 - allocated_items
    if remaining_slots > 0:
        for category, _ in sorted_categories:
            additional_items = news_collection.find(
                {'category': category, '_id': {'$nin': excluded_object_ids}}).limit(remaining_slots)
            for item in additional_items:
                if item not in recommended_news:
                    recommended_news.append(item)
                    remaining_slots -= 1
                    if remaining_slots == 0:
                        break
            if remaining_slots == 0:
                break

    return list_serial_news(recommended_news)


@router.post('/update_behavior')
async def update_behavior(user_behavior: dict):
    print(user_behavior)
    res = user_behavior_collection.find_one(
        {'user_email': user_behavior['userEmail']})
    if not res:
        user = user_collection.find_one({'email': user_behavior['userEmail']})
        if user:
            serialized_user = individual_serial_users(user)
            user_behavior_collection.insert_one({
                'user_id': serialized_user['id'],
                'user_email': user_behavior['userEmail'],
                'seen_news': [],
                'preference': {
                    "general": 0,
                    "business": 0,
                    "sports": 0,
                    "technology": 0,
                    "entertainment": 0,
                    "health": 0,
                    "science": 0,
                }
            })
            res = user_behavior_collection.find_one(
                {'user_email': user_behavior['userEmail']})

    category_seconds = duration_str_to_seconds(user_behavior['duration'])

    res['preference'][user_behavior['category']] += category_seconds

    total_seconds = sum(res['preference'].values())
    if total_seconds > 0:
        for category in res['preference']:
            res['preference'][category] = (
                res['preference'][category] / total_seconds) * 100

    user_behavior_collection.update_one(
        {'user_email': user_behavior['userEmail']},
        {'$set': {'preference': res['preference']}, '$addToSet': {
            'seen_news': user_behavior['news_id']}}
    )

    return user_behavior
