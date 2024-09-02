from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from typing import Optional
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from sqlmodel.product import Product
from sqlmodel.company_publisher import CompanyPublisher
from functions.product import get_all_publishers

linker_route = APIRouter(
    prefix = '/linker',
    tags=['Linker']
)

@linker_route.get("/companypublisher/nopair", status_code=200)
async def Get_All_NoPair_publisher(jwt_dependency: jwt_dependecy):
    returned = []
    try:
        subquery = session.query(CompanyPublisher.c.publisher)
        results = session.query(Product.c.publisher).filter(Product.c.publisher.notin_(subquery)).distinct().all()
        returned = list(map(get_all_publishers,enumerate(results)))
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"An error ocurred: {e}")
        return []
    finally:
        session.close()
        return returned