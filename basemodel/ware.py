from pydantic import BaseModel

class ware_edited(BaseModel):
    wareCode: str
    editDate: str