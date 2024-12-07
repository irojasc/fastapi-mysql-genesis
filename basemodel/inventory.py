from pydantic import BaseModel
from typing import Optional

class body_list(BaseModel):
    code: str
    qtyNew: int
    qtyOld: int

class InOut_Qty(BaseModel):
    codeTS: Optional[str] = None
    operacion: Optional[str] = None 
    operacion_motivo: Optional[str] = None
    socio_docNum: Optional[str] = None
    ubicacion: Optional[str] = None
    comentario: Optional[str] = None
    list_main: Optional[list[body_list]] = None
    fromWare: Optional[str] = None
    toWare: Optional[str] = None
    curUser: Optional[str] = None
    state: Optional[int] = 3
    fromDate: Optional[str] = None
    toDate: Optional[str] = None
    isFinalState: Optional[bool] = None


#Esto es un modelo para el usuario(frond)
class WareProduct(BaseModel):
    wareCode: Optional[str] = None
    idProduct: Optional[int] = None
    loc: Optional[str] = None
    editDate: Optional[str] = None
    ## ...... falta completar