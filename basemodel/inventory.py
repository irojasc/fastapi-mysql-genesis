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
    list_main: list[body_list]
    fromWare: Optional[str] = None
    curUser: Optional[str] = None
    updateDate: Optional[str] = None