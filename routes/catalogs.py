from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, asc, func, insert, and_
from sqlmodel.ovtg import OVTG
from sqlmodel.oafv import OAFV
from utils.validate_jwt import jwt_dependecy
from config.db import con, session

catalog_route = APIRouter(
    prefix = '/catalog',
    tags=['Catalog']
)


@catalog_route.get("/tax_types/")
async def Get_Taxes(type: str = None , jwt_dependency: jwt_dependecy = None):
    returned_value = []
    try:
        #nueva consulta
        if type is not None and type == 'p': #purchase
            stmt = (select(OVTG).filter(OVTG.c.IsActive == 1))
            returned_value = session.execute(stmt).mappings().all()
        if type is not None and type == 's': #sell
            stmt = (select(OAFV).filter(OAFV.c.IsActive == 'Y'))
            returned_value = session.execute(stmt).mappings().all()
    except Exception as e:
        session.rollback()
        session.close()
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return [dict(item) for item in returned_value]
