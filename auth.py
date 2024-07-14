import os
from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.exc import OperationalError
from utils.dictionary2obj import dict2obj
from models.user import User
from config.db import con, session, SECRET_KEY
from sqlalchemy import select

router = APIRouter(
    prefix = '/auth',
    tags=['auth']
)

TOKEN_SECONDS_EXPIRATION = 1800
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest (BaseModel):
    username: str
    password: str

class Token(BaseModel):
    userId: int
    userName: str
    access_token: str
    token_type: str

# @router.post("/", status_code=status.HTTP_201_CREATED)
# async def create_user(create_user_request: CreateUserRequest):
#     pass
#     # create_user_model = Users(
#     #     username=create_user_request.username,
#     #     hashed_password=bcrypt_context.hash(create_user_request.password),
#     # )
#     # db.add(create_user_model)
#     # db.commit()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not authorized')
        raise HTTPException(status_code=401, detail='User not authorized')
    
    token = create_access_token(user.id, user.usr, timedelta(seconds=TOKEN_SECONDS_EXPIRATION))
    return {'userId': user.id, 'userName': user.usr, 'access_token': token, 'token_type': 'bearer'}


def authenticate_user(username: str, password:str):
    Response = False
    try:
        # response = con.execute(select(User.c.id, User.c.user, User.c.pw).where((User.c.user == username))).first()
        response = session.execute(select(User.c.id, User.c.user, User.c.pw).where((User.c.user == username))).first()
        # session.commit()
        (id, usr, pw)  =  (response if response is not None else (None, None, None))
        if not usr:
            Response = False
        else:
            if bool(bcrypt_context.verify(password, pw)):
                Response = dict2obj({"id": id, "usr": usr})
    except:
        session.rollback()
        Response = False
        # raise
        # return False
    finally:
        session.close()
        return Response

def create_access_token(user_id: int, username: str, expires_delta: timedelta):
    encode = {'id': user_id, 'username': username}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: int = payload.get('id')
#         username: str = payload.get('username')
#         if username is None or user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#             detail='Could not validate user.')
#         return {'id': user_id, 'username': username}
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#         detail='Could not validate user.')