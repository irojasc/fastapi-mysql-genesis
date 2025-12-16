from sqlalchemy import (
    Table,
    Column,
    SmallInteger,
    String,
    DateTime,
    DECIMAL,
    Integer
)
from config.db import meta, engine
from sqlalchemy.dialects.mysql import BIGINT

SalesOrderDetail = Table("SalesOrderDetail", meta, 
                Column("LineNum", Integer, nullable=False, unique=True, primary_key=True, autoincrement=True), 
                Column("DocEntry", BIGINT(unsigned=True), nullable=False),
                Column("idProduct", SmallInteger, nullable=False), 
                Column("Quantity", SmallInteger,  nullable=False), 
                Column("UnitPrice",DECIMAL(7, 2), nullable=False),
                Column("DiscSum", DECIMAL(7, 2), nullable=False),
                Column("LineTotal", DECIMAL(7, 2), nullable=False),
                Column("VatSum", DECIMAL(7, 2), nullable=False),
                Column("Total", DECIMAL(7, 2), nullable=False),
                Column("idWare", Integer, nullable=True),
                Column("Uom", String(3), nullable=True),
                Column("VatPrcnt", DECIMAL(7, 2), nullable=False),
                Column("Oafv", String(2), nullable=True),
                Column("Ovtg",String(8), nullable=True),
                Column("CreateDate", DateTime, nullable=True),
                Column("UpdateDate", DateTime, nullable=True)
                )
meta.create_all(bind=engine)