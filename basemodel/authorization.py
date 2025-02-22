from pydantic import BaseModel
from typing import List, Tuple


class auth_data(BaseModel):
    auth_data: List[Tuple[str,str,bool]]
    user_affected: str = None