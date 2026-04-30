from sqlalchemy import (
    Column, Integer, Table, Column, String, Enum, DECIMAL, 
    text, DateTime
)
from sqlalchemy.dialects.mysql import INTEGER #, SMALLINT
from config.db import meta, engine
# from sqlalchemy.sql.sqltypes import String, SmallInteger, DECIMAL

Orders = Table(
            "orders", meta,
            # 1. IDENTIFICADORES
            Column("DocEntry", INTEGER(unsigned=True), primary_key=True, autoincrement=True),
            Column("DocNum", INTEGER(unsigned=True), unique=True, nullable=False),
            Column("cardCode", String(15), nullable=False),

            # 2. RESPONSABLES Y UBICACIÓN
            Column("idWare", Integer, nullable=True),
            Column("SlpCode", String(15), nullable=True),

            # 3. DATOS DE CONTACTO Y ENVÍO
            Column("C_Name", String(250), nullable=False),
            Column("C_DocType", Enum('DNI', 'CE', 'PAS'), nullable=False),
            Column("C_DocNum", String(20), nullable=False),
            Column("C_Email", String(150), nullable=False, index=True),
            Column("C_Phone", String(25), nullable=False),

            # DATOS DE FACTURACIÓN
            Column("DocType", Enum('DNI', 'RUC', 'CE', 'PAS'), nullable=False),
            Column("DocNumId", String(20), nullable=False),
            Column("BillName", String(250)),

            # 4. LOGÍSTICA Y UBIGEO
            Column("ShipType", Enum('TIENDA', 'DELIVERY'), nullable=False),
            Column("idUbigeo", Integer, nullable=True),
            Column("AddressLine", String(255)),
            Column("AddressRef", String(255)),
            Column("TrackingToken", String(12), unique=True, index=True),

            # 5. TOTALES, MONEDA Y DESCUENTOS
            Column("CurrCode", String(3), server_default="PEN"),
            Column("DocTotal", DECIMAL(12, 4), nullable=False),
            Column("DiscSum", DECIMAL(12, 4), server_default=text("0.0000")),
            Column("VatSum", DECIMAL(12, 4), nullable=False),
            Column("ShipSum", DECIMAL(12, 4), server_default=text("0.0000")),
            Column("DocSum", DECIMAL(12, 4), nullable=False),

            # ESTADO Y PASARELA
            Column("DocStatus", Enum('PEND', 'PAGD', 'PROC', 'CAMI', 'ENTR', 'CANC'), server_default="PEND"),
            #PEND:PENDIENTE, PAGD:PAGADO, PROC:PROCESO, CAMI:EN CAMINO, ENTR:ENTREGADO, CANC:CANCELADO
            Column("PayGroup", Enum('MP', 'CQ', 'ST', 'TR'), nullable=False),
            #MP, MERCADO PAGO, CQ: CULQUI, ST: STRIPE, TR: TRASACCION
            Column("TransID", String(100)),
            #TransID, codigo que devuelve el proveedor

            # AUDITORÍA
            Column("CreateDate", DateTime, nullable=True),
            Column("UpdateDate", DateTime, nullable=True),
            
            # Opciones de la tabla para MySQL
            # mysql_engine="InnoDB",
            # mysql_charset="utf8mb4",
            # mysql_collate="utf8mb4_unicode_ci"
)
meta.create_all(bind=engine)