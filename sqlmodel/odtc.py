from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, BINARY, Boolean
from config.db import meta, engine

ODTC = Table("ODTC", meta, 
                Column("DocType", String(10), primary_key=True), 
                Column("DocName", String(100), nullable=False), 
                Column("SunatCode", String(5), nullable=False)
                )
meta.create_all(bind=engine)