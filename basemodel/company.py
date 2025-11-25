from pydantic import BaseModel, root_validator
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

    # # 👉 Nuevo campo
    # id_documento: Optional[int] = None
    # # fecha_creacion: Optional[str] = None <--estara controlado por los datos del  backen

    # @root_validator(pre=True)
    # def set_id_documento(cls, values):
    #     tipo = values.get("tipo_documento")

    #     if tipo is None:
    #         values["id_documento"] = None
    #     else:
    #         tipo_upper = tipo.upper()
    #         if tipo_upper == "SD": #sin documento
    #             values["id_documento"] = 0
    #         elif tipo_upper == "DNI": #dni
    #             values["id_documento"] = 1
    #         elif tipo_upper == "RUC": #ruc
    #             values["id_documento"] = 2
    #         elif tipo_upper == "CE": #carnet de extranjeria
    #             values["id_documento"] = 3
    #         elif tipo_upper == "PAS": #pasaporte
    #             values["id_documento"] = 4
    #         else:
    #             values["id_documento"] = None

    #     return values


