from pydantic import BaseModel
from typing import List

class ubigeo(BaseModel):
    name: str
    id: int

class company(BaseModel):
    DocNum: str
    DocName: str
    DocAddress: str
    DocDepartamento: ubigeo
    DocProvincia: ubigeo
    DocDistrito: ubigeo
    DocEmail: str
    DocPhone: str
    TipoEmpresa: str


