from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text
from utils.validate_jwt import jwt_dependecy
from sqlmodel.ware import Ware
from sqlmodel.wareset import WareSet
from config.db import get_db
from sqlalchemy.orm import Session

warehouse_route = APIRouter(
    prefix = '/warehouse',
    tags=['Ware House']
)

@warehouse_route.get("/", status_code=200)
# def get_ware_house(jwt_dependency: jwt_dependecy):
def get_ware_house(session: Session = Depends(get_db)):
    returned = False
    try:
        data = session.query(Ware.c.id, 
                             Ware.c.code, 
                             Ware.c.isVirtual, 
                             Ware.c.enabled, 
                             WareSet, 
                             Ware.c.isPos, 
                             Ware.c.inv_allowed, 
                             Ware.c.inv_clean, 
                             Ware.c.inv_date).\
        join(WareSet, Ware.c.warelvl == WareSet.c.lvl).\
        all()
        
        result  = list(map(lambda x: {"id": x[0], 
                                      "cod": x[1], 
                                      "auth": {"isVirtual": x[2]!=b'\x00', 
                                               "enabled": x[3]!=b'\x00', 
                                               "locTooltip": x[5]!=b'\x00', 
                                               "isPos": x[-4]!=b'\x00',
                                               "inv_allowed": x[-3]!=b'\x00',
                                               "inv_clean": x[-2]!=b'\x00',
                                               "inv_date": x[-1] or None,
                                               }}, data))
        returned = {"result": result}
    except Exception as e:
        session.close()
        print(f"get_ware_house:get:An error ocurred: {e}")
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        session.close()
        session.rollback()
    finally:
        session.close()
        return returned
