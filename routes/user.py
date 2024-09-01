from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from utils.validate_jwt import jwt_dependecy
from sqlmodel.user import User
from config.db import con

user_route = APIRouter(
    prefix = '/user',
    tags=['User']
)


@user_route.get("/")
# def get_users(access_token: Annotated[str | None, Cookie()] = None):
def get_users(jwt_dependency: jwt_dependecy):
    if not(jwt_dependency):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        # dataUsr = con.execute(select(User.c.user).where((User.c.user == data_user["user"]))).first()
        dataUsrs = con.execute(select(User)).fetchall()
        result  = list(map(lambda x: {"id": x[0], "user": x[3], "enabled": bool(x[5])}, dataUsrs))
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
