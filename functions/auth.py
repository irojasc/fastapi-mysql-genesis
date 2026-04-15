from config.db import SECRET_KEY, ALGORITHM
from sqlalchemy import select
from utils.dictionary2obj import dict2obj
from passlib.context import CryptContext
from datetime import timedelta, datetime
from jose import jwt
from sqlmodel.user import User
from sqlalchemy.orm import Session

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def authenticate_user(
        username: str, 
        password:str,
        sessionx:Session
        ):
    Response = False
    try:
        response = sessionx.execute(select(User.c.id, User.c.user, User.c.pw).where((User.c.user == username))).first()
        (id, usr, pw)  =  (response if response is not None else (None, None, None))
        if not usr:
            Response = False
        else:
            if bool(bcrypt_context.verify(password, pw)):
                Response = dict2obj({"id": id, "usr": usr, "pw": pw})
    except:
        print("rollback")
        sessionx.rollback()
        Response = False

    return Response
    
def create_access_token(user_id: int, username: str, hours: int, minutes: int):
    encode = {'id': user_id, 'username': username}
    # expires = datetime.utcnow() + timedelta(minutes=int(minutes))
    expires = datetime.utcnow() + timedelta(hours=int(hours))
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)