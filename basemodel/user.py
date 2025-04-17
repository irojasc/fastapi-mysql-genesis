from pydantic import BaseModel

class new_user(BaseModel):
    docNumber: str
    userName: str
    user: str
    pwd: str
    creationDate: str
    editDate: str