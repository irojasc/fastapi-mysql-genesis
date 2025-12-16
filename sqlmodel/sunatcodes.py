from sqlalchemy import (
    Table, 
    Column, 
    SmallInteger, 
    String,
    Index
)
from sqlalchemy.dialects.mysql import TINYINT
from config.db import meta, engine

SunatCodes = Table("SunatCodes", meta, 
        Column("Code", SmallInteger, primary_key=True, nullable=False),
        Column("Dscp", String(50), nullable=False),
        Column("IsFinal", TINYINT(unsigned=True), nullable=False, server_default="0")
        )
meta.create_all(bind=engine)