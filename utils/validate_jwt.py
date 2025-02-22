import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from typing import Annotated
from jose import jwt, JWTError
from config.db import SECRET_KEY

ALGORITHM = os.getenv("ALGORITHM_KEY", default=None)
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='Login/token')

async def get_jwt_validation(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True, payload['username']
    except JWTError:
        return False, None

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
