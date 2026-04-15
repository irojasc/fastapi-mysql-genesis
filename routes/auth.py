import os
# from sqlalchemy.exc import OperationalError
# from starlette import status
# from sqlalchemy.orm import Session
# from jose import JWTError
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from basemodel.token import Token
from functions.auth import authenticate_user, create_access_token
from sqlalchemy.orm import Session
from config.db import get_db

auth_route = APIRouter(
    prefix = '/Login',
    tags=['Login']
)

TOKEN_HOURS_EXPIRATION = os.getenv("TOKEN_HOURS_EXPIRATION", default=None)

@auth_route.post("/token", response_model=Token)
# async def login_for_access_token(
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    sessionx: Session = Depends(get_db)
    ):
    user = authenticate_user(form_data.username, 
                             form_data.password,
                             sessionx)
    if not user:
        raise HTTPException(status_code=401, detail='User not authorized')
    token = create_access_token(user.id, user.usr, minutes=None, hours=TOKEN_HOURS_EXPIRATION)
    # token = create_access_token(user.id, user.usr, minutes=TOKEN_HOURS_EXPIRATION, hours=None)
    return {'userId': user.id, 'userName': user.usr, 'hashed': user.pw, 'access_token': token, 'token_type': 'bearer'}
