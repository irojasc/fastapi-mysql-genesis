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

auth_route = APIRouter(
    prefix = '/Login',
    tags=['Login']
)

TOKEN_HOURS_EXPIRATION = os.getenv("TOKEN_HOURS_EXPIRATION", default=None)

@auth_route.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail='User not authorized')
    token = create_access_token(user.id, user.usr, hours=TOKEN_HOURS_EXPIRATION)
    return {'userId': user.id, 'userName': user.usr, 'access_token': token, 'token_type': 'bearer'}
















# auth_route
#.post("/", status_code=status.HTTP_201_CREATED)
# async def create_user(create_user_request: CreateUserRequest):
#     pass
#     # create_user_model = Users(
#     #     username=create_user_request.username,
#     #     hashed_password=bcrypt_context.hash(create_user_request.password),
#     # )
#     # db.add(create_user_model)
#     # db.commit()

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