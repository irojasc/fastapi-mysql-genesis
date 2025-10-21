from config.db import con, session, SECRET_KEY, ALGORITHM
from sqlalchemy import select
from utils.dictionary2obj import dict2obj
from passlib.context import CryptContext
from datetime import timedelta, datetime
from jose import jwt
from sqlmodel.user import User

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

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
                Response = dict2obj({"id": id, "usr": usr, "pw": pw})
    except:
        print("rollback")
        session.rollback()
        Response = False
        # raise
        # return False
    finally:
        session.close()
        return Response
    
def create_access_token(user_id: int, username: str, hours: int, minutes: int):
    encode = {'id': user_id, 'username': username}
    # expires = datetime.utcnow() + timedelta(minutes=int(minutes))
    expires = datetime.utcnow() + timedelta(hours=hours)
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Ejemplo chat gpt
# def create_access_token(user_id: int, username: str, hours: int = 0, minutes: int = 30):
#     encode = {
#         "id": user_id,
#         "username": username
#     }
#     expires = datetime.utcnow() + timedelta(hours=hours, minutes=minutes)
#     encode.update({"exp": expires})
#     return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# token = create_access_token(1, "ivan", hours=1, minutes=30)
# print(token)