from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String, SmallInteger, DECIMAL
from config.db import meta, engine

OVTG = Table("Ovtg", meta, 
                Column("VatCode", String(8), primary_key=True), 
                Column("VatName", String(50), nullable=False), 
                Column("Rate", DECIMAL(8, 2), nullable=False),
                Column("IsActive", SmallInteger, nullable=False, server_default="1")
                )
meta.create_all(bind=engine)