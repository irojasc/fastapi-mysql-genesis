from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    String,
    Integer,
    DateTime,
    SmallInteger,
    Text
)
from config.db import meta, engine
from sqlalchemy.dialects.mysql import BIGINT

SalesOrderSunat = Table("SalesOrderSunat", meta, 
                Column("Id", BIGINT(unsigned=True), primary_key=True, autoincrement=True),
                Column("DocEntry", BIGINT(unsigned=True), nullable=False),
                Column("Status", SmallInteger, nullable=True), 
                Column("CancelDate", DateTime, nullable=True), 
                Column("CancelReason", String(255), nullable=True),
                Column("Hash", String(255), nullable=True),
                Column("QR", Text, nullable=True),
                Column("SendDate", DateTime, nullable=True),
                Column("SunatLastCheck", DateTime, nullable=True),
                Column("CreateDate", DateTime, nullable=True),
                Column("UpdateDate", DateTime, nullable=True),
                Column("Ticket", String(50), nullable=True)
                )
meta.create_all(bind=engine)