from fastapi import APIRouter, HTTPException, Depends
# from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text
from utils.validate_jwt import jwt_dependecy
from sqlmodel.ware import Ware
from sqlmodel.wareset import WareSet
from config.db import get_db
from sqlalchemy.orm import Session
#from fastapi import APIRouter, HTTPException, Depends

warehouse_route = APIRouter(
    prefix = '/warehouse',
    tags=['Ware House']
)

@warehouse_route.get("/", status_code=200)
def get_ware_house(sessionx: Session = Depends(get_db)):
    returned = False
    try:
        data = sessionx.query(Ware.c.id, 
                             Ware.c.code, 
                             Ware.c.isVirtual, 
                             Ware.c.enabled, 
                             WareSet.c.locTooltip, 
                             Ware.c.isPos, 
                             Ware.c.inv_allowed, 
                             Ware.c.inv_clean, 
                             Ware.c.inv_date).\
        join(WareSet, Ware.c.warelvl == WareSet.c.lvl).\
        all()
        
        result  = list(map(lambda x: {"id": x.id, 
                                      "cod": x.code, 
                                      "auth": {"isVirtual": x.isVirtual != b'\x00', 
                                               "enabled": x.enabled != b'\x00', 
                                               "locTooltip": x.locTooltip != b'\x00', 
                                               "isPos": x.isPos != b'\x00',
                                               "inv_allowed": x.inv_allowed != b'\x00',
                                               "inv_clean": x.inv_clean != b'\x00',
                                               "inv_date": x.inv_date or None,
                                               }}, data))
        returned = {"result": result}

    except SQLAlchemyError as e: # Primero la específica
        sessionx.rollback()
        print(f"SQLAlchemy Error: {e}")
        returned = {"result": [], "error": "Database error"}
    except Exception as e: # Luego la general
        print(f"General Error: {e}")
        returned = {"result": [], "error": str(e)}
    
    return returned