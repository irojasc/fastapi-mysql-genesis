from sqlalchemy import (
    Column, Integer, Table, Column, String, Enum, DECIMAL, 
    text, DateTime
)
from config.db import meta, engine
from sqlalchemy.dialects.mysql import INTEGER, SMALLINT
# from sqlalchemy.sql.sqltypes import String, SmallInteger, DECIMAL

OrderDetails = Table(
                "orderdetails", meta,
                # 1. IDENTIFICADORES Y LLAVE PRIMARIA COMPUESTA
                Column("DocEntry", INTEGER(unsigned=True), primary_key=True),
                Column("LineNum", SMALLINT(unsigned=True), primary_key=True),
                # 2. PRODUCTO Y CANTIDAD
                Column("idProduct", Integer, nullable=False, index=True),
                Column("Quantity", INTEGER(unsigned=True), nullable=False),
                # 3. PRECIOS Y TOTALES (Respetando precisiones del SQL)
                Column("UnitPrice", DECIMAL(12, 2), nullable=False),
                Column("DiscSum", DECIMAL(12, 4), nullable=False, server_default=text("'0.0000'")),
                Column("LineTotal", DECIMAL(12, 4), nullable=False),
                Column("VatSum", DECIMAL(12, 4), nullable=False),
                Column("Total", DECIMAL(12, 2), nullable=False),

                # 4. ATRIBUTOS ADICIONALES (SAP/Logística)
                Column("Uom", String(3), nullable=True),
                Column("VatPrcnt", DECIMAL(5, 2), nullable=False),
                Column("Oafv", String(2), nullable=True),
                Column("Ovtg", String(8), nullable=True),

                # 5. AUDITORÍA (Tal como pediste en el ALTER anterior, por defecto NULL)
                Column("CreateDate", DateTime, nullable=True),
    )
meta.create_all(bind=engine)