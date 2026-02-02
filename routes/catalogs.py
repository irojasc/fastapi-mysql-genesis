from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, asc, func, insert, and_
from sqlmodel.ovtg import OVTG
from sqlmodel.oafv import OAFV
from sqlmodel.language import Language
from sqlmodel.categories import Categories
from utils.validate_jwt import jwt_dependecy
from functions.catalogs import group_categories_by_family
from config.db import con, session
from datetime import datetime, timezone
import pytz

catalog_route = APIRouter(
    prefix = '/catalog',
    tags=['Catalog']
)

@catalog_route.get("/time")
async def Get_Time(jwt_dependency: jwt_dependecy = None):
    # Hora UTC
    now_utc = datetime.now(timezone.utc)

    # Hora de Lima (UTC-5)
    lima_tz = pytz.timezone("America/Lima")
    now_lima = now_utc.astimezone(lima_tz)

    # Retornar como diccionario (JSON)
    return {
        "utc": now_utc.isoformat(),
        "lima": now_lima.isoformat(),
        "lima_bd_format": now_lima.strftime("%Y-%m-%d %H:%M:%S"),
        "lima_transfer_format": now_lima.strftime("%Y-%m-%d")
    }

@catalog_route.get("/tax_types/")
async def Get_Taxes(type: str = None , jwt_dependency: jwt_dependecy = None):
    returned_value = []
    try:
        #nueva consulta
        if type is not None and type == 'p': #purchase
            stmt = (select(OVTG).filter(OVTG.c.IsActive == 1))
            returned_value = session.execute(stmt).mappings().all()
        
        
        if type is not None and type == 's': #sell
            stmt = (
                    select(OAFV, OVTG.c.Rate)
                    .join(OVTG, OAFV.c.VatCode == OVTG.c.VatCode)
                    .filter(OAFV.c.IsActive == 'Y'))
            returned_value = session.execute(stmt).mappings().all()
    except Exception as e:
        session.rollback()
        session.close()
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return [dict(item) for item in returned_value]

@catalog_route.get("/tax_types/")
async def Get_Taxes(type: str = None , jwt_dependency: jwt_dependecy = None):
    returned_value = []
    try:
        #nueva consulta
        if type is not None and type == 'p': #purchase
            stmt = (select(OVTG).filter(OVTG.c.IsActive == 1))
            returned_value = session.execute(stmt).mappings().all()
        
        
        if type is not None and type == 's': #sell
            stmt = (
                    select(OAFV, OVTG.c.Rate)
                    .join(OVTG, OAFV.c.VatCode == OVTG.c.VatCode)
                    .filter(OAFV.c.IsActive == 'Y'))
            returned_value = session.execute(stmt).mappings().all()
    except Exception as e:
        session.rollback()
        session.close()
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return [dict(item) for item in returned_value]

@catalog_route.get("/languages/")
async def Get_Languages(jwt_dependency: jwt_dependecy = None):
    returned_value = []
    try:
        #nueva consulta
        stmt = (select(Language.c.id.label('idLang'), Language.c.code.label('codeLang'), Language.c.language.label('nameLang')))
        returned_value = session.execute(stmt).mappings().all()
        returned_value = [dict(lang) for lang in returned_value]

    except Exception as e:
        session.rollback()
        session.close()
        returned_value = []
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return returned_value

@catalog_route.get("/categories/")
async def Get_Product_Category(jwt_dependency: jwt_dependecy = None):
    returned_value = []
    try:
        #nueva consulta
        stmt = (select(Categories.c.id, 
                       Categories.c.Level.label('level'), 
                       Categories.c.Name.label('name'),
                       Categories.c.idParent)
                )
        response = session.execute(stmt).mappings().all()
        returned_value = group_categories_by_family(categories=response)

    except Exception as e:
        session.rollback()
        session.close()
        returned_value = []
        print(f"An error ocurred: {e}")
    finally:
        session.close()
        return returned_value
