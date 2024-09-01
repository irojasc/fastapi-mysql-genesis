from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from utils.validate_jwt import jwt_dependecy
from sqlmodel.company import Company
from functions.company import get_all_companies

company_route = APIRouter(
    prefix = '/company',
    tags=['Company']
)


@company_route.get("/", status_code=200)
async def Get_All_Companies(jwt_dependency: jwt_dependecy):
    # stmt = select(Company)
    try:
        results = session.query(Company).all()
        returned = list(map(get_all_companies,results))
        return returned
    except Exception as e:
        print(f"An error ocurred: {e}")



@company_route.get("/supplier", status_code=200)
async def Get_All_Suppliers(jwt_dependency: jwt_dependecy):
    try:
        results = session.query(Company).where(Company.c.type == 'S').all()
        returned = list(map(get_all_companies,results))
        return returned
    except Exception as e:
        print(f"An error ocurred: {e}")
        return []