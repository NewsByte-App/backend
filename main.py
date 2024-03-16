from fastapi import FastAPI
from routes.route import router
from fastapi_pagination import Page, add_pagination, paginate


app = FastAPI()
add_pagination(app)

app.include_router(router)
