from pydantic import BaseModel
from typing import List

class linker_(BaseModel):
    publisher: str
    docNum: str

class linker_list(BaseModel):
    data: List[linker_]