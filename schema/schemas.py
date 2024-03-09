from datetime import datetime


def individual_serial_news(news) -> dict:
    return {
        "_id": str(news["_id"]),
        "title": news.get('title', ''),
        "content": news.get('content', ''),
        "summary": news.get('summary', ''),
        "source_url": news.get('url', ''),
        "image_url": news.get('image_url', ''),
        "description": news.get("description", ''),
        "published_date": news.get('published_date'),
        "category":  news.get('category', ''),
        "author":  news.get('author', ''),
    }


def list_serial_news(news) -> list:
    return [individual_serial_news(n) for n in news]


def individual_serial_users(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "loginType": user["loginType"],
        "user_preferences": dict(user["user_preferences"])
    }


def list_serial_users(users) -> list:
    return [individual_serial_users(n) for n in users]
