from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from utils.validate_jwt import jwt_dependecy
from sqlmodel.warehouse import WareHouse
from sqlmodel.wareset import WareSet
from config.db import con

warehouse_route = APIRouter(
    prefix = '/warehouse',
    tags=['Ware House']
)

@warehouse_route.get("/")
def get_ware_house(jwt_dependency: jwt_dependecy):
    if not(jwt_dependency):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        # dataUsr = con.execute(select(User.c.user).where((User.c.user == data_user["user"]))).first()
        # dataUsrs = con.execute(select(WareHouse)).fetchall()
        dataUsrs = con.execute(select(WareHouse.c.id, WareHouse.c.code, WareHouse.c.isVirtual, WareHouse.c.enabled, WareSet).select_from(WareHouse.join(WareSet, WareHouse.c.warelvl == WareSet.c.lvl)))
        data = dataUsrs.fetchall()
        keys = list(dataUsrs.keys())
        result  = list(map(lambda x: {"id": x[0], "cod": x[1], "auth": {"isVirtual": x[2]!=b'\x00', "enabled": x[3]!=b'\x00', keys[5]: x[5]!=b'\x00'}}, data))
        return JSONResponse(
            status_code=200,
            content={"result": result}
            )
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
