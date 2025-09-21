from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String, SmallInteger
from config.db import meta, engine

UOM = Table("Uom", meta, 
                Column("UomCode", String(3), primary_key=True), 
                Column("UomName", String(30), nullable=False), 
                Column("IsActive", SmallInteger, nullable=False, server_default="1")
                )
meta.create_all(bind=engine)