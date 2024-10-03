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

@warehouse_route.get("/")
def get_ware_house(jwt_dependency: jwt_dependecy):
    returned = False
    try:
        if not(jwt_dependency):
            raise HTTPException(
                status_code=498,
                detail='Invalid Access Token',
            )
        else:
            # dataUsrs = con.execute(select(Ware.c.id, Ware.c.code, Ware.c.isVirtual, Ware.c.enabled, WareSet).select_from(Ware.join(WareSet, Ware.c.warelvl == WareSet.c.lvl)))
            data = session.query(Ware.c.id, Ware.c.code, Ware.c.isVirtual, Ware.c.enabled, WareSet).\
            join(WareSet, Ware.c.warelvl == WareSet.c.lvl).\
            all()
            #get colums name of selected table with session sqlalchemy?
            #select specific columns with session and join tables sqlalchemy?
            # data = dataUsrs.fetchall()
            # keys = list(dataUsrs.keys())
            result  = list(map(lambda x: {"id": x[0], "cod": x[1], "auth": {"isVirtual": x[2]!=b'\x00', "enabled": x[3]!=b'\x00', "locTooltip": x[5]!=b'\x00'}}, data))
            returned = {"result": result}
            # return JSONResponse(
            #     status_code=200,
            #     content={"result": result}
            #     )
    except Exception as e:
        print(f"get_ware_house/nopair:get:An error ocurred: {e}")
    except SQLAlchemyError as e:
        print("An SqlAlchemmy happened ", e)
        session.rollback()
    finally:
        session.close()
        return returned

        # try:
        #     data_user = jwt.decode(access_token, key=SECRET_KEY, algorithms=["HS256"])
        #     dataUsr = con.execute(select(User.c.user).where((User.c.user == data_user["user"]))).first()
        #     if dataUsr is None:
        #         raise HTTPException(
        #     status_code=498,
        #     detail='Invalid Access Token',
        #     )
        #     else:
        #         dataFetched = con.execute(User.select()).fetchall()
        #         print(dataFetched)
                
        #         usersList = list(map(lambda x: {"doc": x[2], "user": x[3], "enabled": bool(x[5])},dataFetched))
        #         return {
        #             "result": usersList
        #         }
        # except JWTError:
        #     raise HTTPException(
        #     status_code=498,
        #     detail='Invalid Access Token',
        # )
