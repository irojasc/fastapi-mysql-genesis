from pydantic import BaseModel
from typing import List, Optional

class BankAccount(BaseModel):
    id: Optional[int] = None
    tipo_cuenta: Optional[str] = None
    banco: Optional[str] = None
    n_cuenta: Optional[str] = None
    n_cci: Optional[str] = None
    titular: Optional[str] = None

class Contact(BaseModel):
    id: Optional[int] = None
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    default: Optional[int] = None


class BusinessPartner(BaseModel):
    tipo_socio: Optional[str] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    nombre: Optional[str] = None
    nombre_comercial: Optional[str] = None
    direccion: Optional[str] = None
    departamento: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    estado: Optional[str] = None
    condicion: Optional[str] = None
    condicion_pago: Optional[str] = None
    contactos: Optional[List[Contact]] = None
    cuenta_bancaria: Optional[List[BankAccount]] = None
    usuario_creacion: Optional[str] = None
    moneda: Optional[str] = None
    # fecha_creacion: Optional[str] = None <--estara controlado por los datos del  backen


