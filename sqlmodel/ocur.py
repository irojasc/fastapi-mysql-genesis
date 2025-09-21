from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String, SmallInteger
from config.db import meta, engine

OCUR = Table("Ocur", meta, 
                Column("CurrCode", String(3), primary_key=True), 
                Column("CurrName", String(50), nullable=False), 
                Column("CurrNum", SmallInteger, nullable=False),
                )
meta.create_all(bind=engine)