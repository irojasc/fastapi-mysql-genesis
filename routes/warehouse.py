from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text
from utils.validate_jwt import jwt_dependecy
from sqlmodel.ware import Ware
from sqlmodel.wareset import WareSet
from config.db import con, session

warehouse_route = APIRouter(
    prefix = '/warehouse',
    tags=['Ware House']
)

@warehouse_route.get("/", status_code=200)
# def get_ware_house(jwt_dependency: jwt_dependecy):
def get_ware_house():
    returned = False
    try:
        # if not(jwt_dependency):
        #     raise HTTPException(
        #         status_code=498,
        #         detail='Invalid Access Token',
        #     )
        # else:
        # dataUsrs = con.execute(select(Ware.c.id, Ware.c.code, Ware.c.isVirtual, Ware.c.enabled, WareSet).select_from(Ware.join(WareSet, Ware.c.warelvl == WareSet.c.lvl)))
        data = session.query(Ware.c.id, Ware.c.code, Ware.c.isVirtual, Ware.c.enabled, WareSet, Ware.c.isPos, Ware.c.inv_allowed, Ware.c.inv_clean, Ware.c.inv_date).\
        join(WareSet, Ware.c.warelvl == WareSet.c.lvl).\
        all()
        #get colums name of selected table with session sqlalchemy?
        #select specific columns with session and join tables sqlalchemy?
        # data = dataUsrs.fetchall()
        # keys = list(dataUsrs.keys())
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
