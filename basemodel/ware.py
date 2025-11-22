from pydantic import BaseModel
from typing import Optional

class ware_edited(BaseModel):
    wareCode: str
    editDate: Optional[str] = None