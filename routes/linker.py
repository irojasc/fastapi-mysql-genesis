from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from typing import Optional
from utils.validate_jwt import jwt_dependecy
from config.db import con, session
from sqlmodel.product import Product
from sqlmodel.company_publisher import CompanyPublisher
from functions.product import get_all_publishers, get_all_pair_company_publishers
from basemodel.linker import linker_list
from sqlalchemy import insert, delete

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
        print(f"companypublisher/nopair:get:An error ocurred: {e}")
        return []
    finally:
        session.close()
        return returned

@linker_route.get("/companypublisher/pair", status_code=200)
async def Get_All_Pair_publisher(jwt_dependency: jwt_dependecy):
    returned = []
    try:
        results = session.query(CompanyPublisher).all()
        returned = get_all_pair_company_publishers(results)
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"(companypublisher/pair:get):An error ocurred: {e}")
        return []
    finally:
        session.close()
        return returned

@linker_route.post("/companypublisher", status_code=201)
async def post_pairs_company_publisher(linker: linker_list, jwt_dependency: jwt_dependecy):
    try:
        returned = []
        for model in linker.data:
            returned.append({'doc':model.docNum, 'publisher': model.publisher})
        session.execute(insert(CompanyPublisher),returned)
        session.commit()
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"(companypublisher:post):An error ocurred: {e}")
        raise HTTPException(status_code=304, detail="Something wrong happens")
        return []
    finally:
        session.close()
        return []
        # return returned

@linker_route.delete("/companypublisher", status_code=204)
async def delete_pairs_company_publisher(linker: linker_list, jwt_dependency: jwt_dependecy):
    try:
        returned = []
        for model in linker.data:
            returned.append({'doc':model.docNum, 'publisher': model.publisher})
        session.execute(delete(CompanyPublisher).where(CompanyPublisher.c.publisher == returned[0]['publisher']))
        session.commit()
    except Exception as e:
        print("rollback")
        session.rollback()
        print(f"(companypublisher:delete): An error ocurred: {e}")
        raise HTTPException(status_code=304, detail="Something wrong happens")
        return []
    finally:
        session.close() 
        return []
        # return returned