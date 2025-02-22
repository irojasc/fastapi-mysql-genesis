from pydantic import BaseModel
from typing import Optional

# Define a Pydantic model
class product_maintenance(BaseModel):
    rqType: str 
    code: str = ''
    isbn: str = ''
    title: str = '' 
    autor: str = '' 
    publisher: str = '' 
    pvp: str = ''
    pv: str = ''
    asker: str 
    warehouse: str
    date: str

class ware_product_data(BaseModel):
    wareCode: str = None
    exits: bool = None
    active: bool = None
    location: str = None
    stockMin: int = 0
    stockMax: int = 0
    pvp1: float = 0.0
    pvp2: float = 0.0
    dsct: float = 0.0
    isVirtual: bool = None


class ware_product_(BaseModel):
    id: int
    idItem: str
    isbn: Optional[str] = None
    title: str
    autor: str
    publisher: str
    content: Optional[str] = None
    dateOut: Optional[str] = None
    idLanguage: Optional[str] = None
    pages: Optional[int] = None
    weight: Optional[int] = None
    cover: Optional[bool] = None
    width: Optional[int] = None
    height: Optional[int] = None
    creationDate: str = None
    editDate: str
    large: Optional[int] = None
    wholesale: Optional[bool] = None
    antique: Optional[bool] = None
    atWebProm: Optional[bool] = None
    waredata: list[ware_product_data]