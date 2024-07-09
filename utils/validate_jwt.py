from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from jose import jwt, JWTError

SECRET_KEY = 'a40bd8c1de406be2c0398f960f74b3e3a127c4ad4b1a637b0be6e4542df8f634'
ALGORITHM = 'HS256'

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
async def get_jwt_validation(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except JWTError:
        return False

jwt_dependecy = Annotated[bool, Depends(get_jwt_validation)]
     
     
     
#try
# if username is None or user_id is None:
#     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#     detail='Could not validate user.')
# return {'content': product_list}
###################################except
# print("si entra aqui")
# RedirectResponse(url="/", status_code=401)
# raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
# detail='Could not validate user.')