from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from utils.validate_jwt import jwt_dependecy
# from models.user import User

product_route = APIRouter(
    prefix = '/product',
    tags=['Product']
)

product_list = [{"id": 1, "title": "candado"}, {"id": 2, "title": "tranca"}]

@product_route.get("/", status_code=200)
async def get_products(jwt_dependency: jwt_dependecy):
    if jwt_dependency:
        return {
            "content": product_list
        }
    else:
        raise HTTPException(status_code=401, detail='Authentication failed')

