from pydantic import BaseModel, Field
from typing import Optional, List, Dict

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
    id: Optional[str] = None
    idItem: str
    isbn: Optional[str] = None
    title: str
    autor: str
    publisher: Optional[str] = None
    content: Optional[str] = None
    dateOut: Optional[str] = None
    idCategory: Optional[List[Dict]] = Field(default_factory=list)
    idLanguage: Optional[List[Dict]] = Field(default_factory=list)
    pages: Optional[int] = None
    weight: Optional[int] = None
    cover: Optional[bool] = None
    width: Optional[int] = None
    height: Optional[int] = None
    creationDate: Optional[str] = None
    editDate: Optional[str] = None
    large: Optional[int] = None
    wholesale: Optional[bool] = None
    antique: Optional[bool] = None
    atWebProm: Optional[bool] = None
    waredata: list[ware_product_data]
    CardCode: Optional[str]= None
    InvntItem: Optional[str] =  'Y'
    SellItem: Optional[str] =  'Y'
    BuyItem: Optional[str] =  'Y'
    InvntryUom: Optional[str] =  'NIU'
    VatBuy: Optional[str] = None
    VatSell: Optional[str] = None


class product_basic_model(BaseModel):
    DocEntry: Optional[int] = None
    UploadEntry: Optional[int] = None
    FileName: Optional[str] = None
    prevFileName: Optional[str] = None #obtiene nombre anterior de archivo en caso tenga
    ContentType: Optional[str] = None
    ConfirmStatus: Optional[str] = None #P(Pending), C(Completed), F(Failed), E(Expira) 
    FileRole: Optional[str] = None

    