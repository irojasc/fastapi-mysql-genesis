from pydantic import BaseModel
from datetime import date

class new_user(BaseModel):
    docNumber: str
    userName: str
    user: str
    pwd: str
    creationDate: str
    editDate: str