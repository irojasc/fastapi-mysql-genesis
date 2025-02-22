from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, asc, insert, func
from sqlalchemy.exc import SQLAlchemyError
from utils.validate_jwt import jwt_dependecy
from sqlmodel.user import User
from config.db import con, session
from functions.inventory import changeBin2Bool
from basemodel.user import new_user
from utils.hash_handler import hash_password

user_route = APIRouter(
    prefix = '/user',
    tags=['User']
)

@user_route.get("/")
# def get_users(access_token: Annotated[str | None, Cookie()] = None):
def get_users(jwt_dependency: jwt_dependecy):
    # if not(jwt_dependency):
    if not(True):
        raise HTTPException(
            status_code=498,
            detail='Invalid Access Token',
        )
    else:
        try:
            # dataUsrs = con.execute(select(User).order_by(User.c.id.asc())).fetchall()
            # dataUsrs = session.query(User).all()
            dataUsrs = session.query(User).order_by(asc(User.c.id)).all()
            session.close()
            result  = list(map(lambda x: {"id": x[0], "docNum": x[2], "userName": x[8], "user": x[3], "enabled": changeBin2Bool(x[5])}, dataUsrs))
            return JSONResponse(
                status_code=200,
                content={"result": result}
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        
@user_route.post("/", status_code=200)
async def get_last_row(jwt_dependency: jwt_dependecy, new_user: new_user):
    # print(new_user.docNumber, 
    #       new_user.userName, 
    #       new_user.user,
    #       new_user.pwd,
    #       new_user.creationDate,
    #       new_user.editDate,
    #       )
    try:
        max_id = session.query(func.max(User.c.id)).first()

        stmt = (
                insert(User).
                values(
                    id = int(max_id[0]) + 1,
                    idDoc= new_user.docNumber or '',
                    user= new_user.user or '',
                    pw= hash_password(new_user.pwd) or '',
                    editDate= new_user.editDate or '',
                    creationDate= new_user.creationDate or '',
                    userName= new_user.userName or '',
                    )
                )
        response_1 = session.execute(stmt)
        session.commit()
        session.close()
        if(response_1.rowcount > 0):
            pass
        else:
            return HTTPException(status_code=304, detail="Something wrong happens")

    except SQLAlchemyError as e:
        # print(f"Error occurred while executing the statement: {e}")
        session.rollback()  # Rollback the session if there's an error
        raise HTTPException(status_code=304, detail="Error: {e}")

