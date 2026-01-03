
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class series_request(BaseModel):
    SeriesCode: Optional[str] = None #obligatorio
    WareID: Optional[int] = None #obligatorio
    SerieType: Optional[str] = None #obligatorio

class series_internal_def(BaseModel):
    Prefix: Optional[str] = None #obligatorio # prefijo
    NextNumber: Optional[str] = None #obligatorio #ejemplo: 00000001

class series_create_request(BaseModel):
    codigo: Optional[str] = None #obligatorio
    tipoDoc: Optional[str] = None #obligatorio
    almacen: Optional[int] = None #obligatorio
    tipoSerie: Optional[str] = None #obligatorio
    prefijo: Optional[str] = None #obligatorio
    estado: Optional[str] = None #obligatorio


    @field_validator("estado", mode="before")
    def normalize_estado(cls, value):
        if value is None:
            return None
        
        # Validación estricta: debe ser EXACTAMENTE en mayúsculas
        mapping = {
            "ACTIVO": "Active",
            "RESERVADO": "Reserved",
        }

        # Si no está en el mapping, devolver None
        return mapping.get(value, None)

