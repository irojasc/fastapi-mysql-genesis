from sqlalchemy import Table, Column
# from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary, Float, DateTime, DECIMAL
from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    String,
    DateTime,
    DECIMAL,
    Enum,
    Integer
)
from config.db import meta, engine

SalesOrder = Table("SalesOrder", meta,
                Column("DocEntry", BigInteger, nullable=False, unique=True, primary_key=True, autoincrement=True), 
                Column("DocNum", String(20), nullable=True),
                Column("DocType", String(3), nullable=True), 
                Column("DocDate", DateTime,  nullable=True), 
                Column("DocDueDate", DateTime, nullable=True),
                Column("CardCode", String(20), nullable=False),
                Column("SubTotal", DECIMAL(7, 2), nullable=True),
                Column("DiscSum", DECIMAL(7, 2), nullable=True),
                Column("VatSum", DECIMAL(7, 2), nullable=True),
                Column("DocTotal", DECIMAL(7, 2), nullable=True),
                Column("DocStatus", Enum('O', 'C', 'H', 'A', name="doc_status"), default='O'),
                Column("DocCur", String(3), default='PEN'),
                Column("CashBoxTS", String(12), nullable=True),
                Column("RefDocEntry", Integer, nullable=True),
                Column("PymntGroup", Enum('CRDN','CRDS','CASH','WPHN','WMCH','TRAN', name="pymnt_group"), nullable=False, default='CASH'),
                Column("SlpCode", String(15), nullable=False),
                Column("CreateDate", DateTime, nullable=True),
                Column("UpdateDate", DateTime, nullable=True)
                )
meta.create_all(bind=engine)