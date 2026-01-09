
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
# from decimal import Decimal #recomendado para dinero, no pierde por redondeo
from functions.catalogs import get_lima_date_formatted, get_lima_time_formatted
from config.db import MIFACT_MIRUC
import pytz


# Define a Pydantic model
class cash_register(BaseModel):
    CodeTS: Optional[str] = None
    WareID: Optional[int] = None #obligatorio
    User: Optional[str] = None
    OpenDate: Optional[datetime] = None
    CloseDate: Optional[datetime] = None
    Status: Optional[str] = None
    CashOpen: Optional[float] = None
    CashClose: Optional[str] = None
    CashDiff: Optional[str] = "0.00"
    Obs: Optional[str] = None
    UpdateDate: Optional[datetime] = None
    code2count: Optional[str] = None
    total2count: Optional[int] = None

class sales_request(BaseModel):
    WareID: Optional[int] = None #obligatorio
    Date: Optional[str] = None #obligatorio
    IdItem: Optional[int] = 2

class external_document(BaseModel):
    DocEntry: Optional[int] = None #obligatorio
    QR: Optional[str] = None
    Hash: Optional[str] = None
    Status: Optional[int] = None
    SendDate: Optional[datetime] = None
    Ticket: Optional[str] = None
    # pdf_bytes: Optional[str] = None
    # pdf_url: Optional[str] = None


class item(BaseModel):
    id: int
    code: Optional[str] = None
    dscp: str
    uom : str
    qty : str
    ovtg: str
    oafv: str
    ovtg_rate: str
    pv_no_igv: str #VAL_UNIT_ITEM : valor unitario sin igv
    pv_si_igv: str #PRC_VTA_UNIT_ITEM : valor unitario con igv
    total_no_igv: str #VAL_VTA_ITEM : total sin igv sin descuentos
    dsct_user_unit_no_igv: str #: descunto por unidad sin igv
    total_si_igv: str #MNT_PV_ITEM : total con igv (qty * pv)
    # total_solo_igv: str #MNT_IGV_ITEM: total solo igv (qty * pv)
    dsct_user_total_no_igv: str
    VatSum: str #solo igv
    
class sales_order_for_cancel(BaseModel):
    doc_entry: Optional[str] = None
    doc_dscp: Optional[str] = None


class sales_order(BaseModel):
    doc_tipo: Optional[str] = "NV" #nota de venta por defecto
    emisor_nombre : Optional[str] = "MUSEO LIBRERIA GENESIS"
    emisor_doc : Optional[str] = MIFACT_MIRUC
    emisor_correo : Optional[str] = "libreriagenesiscusco@gmail.com"
    receptor_cod : Optional[str] = "C99999999"
    codigo_caja : Optional[str] = None
    fecha_emision : str = Field(default_factory=get_lima_date_formatted, description="Hora de emisión en formato HH:MM:SS (Perú)")
    hora_emision: str = Field(default_factory=get_lima_time_formatted, description="Hora de emisión en formato HH:MM:SS (Perú)")
    total_gravado: str = "0.00"
    total_exonerado: str = "0.00"
    total_igv: str = "0.00"
    total_descuentos: str = "0.00" #<- incluye igv
    VatSum: str = "0.00"
    SubTotal: str = "0.00"
    total_monto: str = "0.00"
    terminos_pago: str = 'CASH' #referencia si es contado, credito, etc.
    forma_pago: str #referencia a pago efectivo, tarjeta , etc.
    id_ware: int
    items: List[item]


class Item_Ticket(BaseModel):
    id: Optional[str] = "0"
    dscp: Optional[str] = "" #agua cielo 1L
    cod: Optional[str] = "" #123654
    qty: Optional[str] = "0" # 1
    pvp: Optional[str] = "0.00" # 10.00 sin igv
    dsct: Optional[str] = "0.00" # 2.00
    total_linea: Optional [str] = "0.00" # 12.00



class Body_Ticket(BaseModel):
    doc_num: Optional[str] = "" #serie-correlativo
    doc_date : Optional[str] = "" #formato 2025-10-07
    card_name : Optional[str] = "" #pontificia universidad catolica del peru
    card_num : Optional[str] = "" #205689741258
    sub_total : Optional[str] = "0.00" #120.00
    dscto_total : Optional[str] = "0.00" #20.00
    tax_total: Optional[str] = "0.00" # %18, 18.00
    total : Optional[str] = "0.00" # 118.00
    pay_method: Optional[str] = "" # Efectivo, Tarjeta
    doc_time: Optional[str] = "" #hora de registro
    items: List[Item_Ticket] = [] #->> 

    model_config = ConfigDict(extra="allow")

class Item_Ticket_Close(BaseModel):
    enum: Optional[str] = "" #agua cielo 1L
    pay_method: Optional[str] = "" #123654
    dscp: Optional[str] = "" # 1
    qty: Optional[str] = "" # 10.00 sin igv
    total_linea: Optional[str] = "0.00" # 2.00
    status: Optional[str] = None

class Body_Ticket_Close(BaseModel):
    caja: Optional[str] = "0.00" #serie-correlativo
    cash_teory : Optional[str] = "0.00" #formato 2025-10-07
    diff : Optional[str] = "0.00" #pontificia universidad catolica del peru
    total : Optional[str] = "0.00" #205689741258
    card_total_walletmch: Optional[str] = "0.00",
    wallet_total_phone: Optional[str] = "0.00",
    date : Optional[str] = "" 
    vendedor : Optional[str] = ""
    items: List[Item_Ticket_Close] = []
    item2Sold: Optional[int] = 0
    item2Total: Optional[int] = 0