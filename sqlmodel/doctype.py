from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String
from config.db import meta, engine

DocType = Table("DocType", meta, 
                Column("DocTypeCode", String(3), primary_key=True), 
                Column("DocTypeName", String(25), nullable=False), 
                Column("SunatCode", String(2), nullable=False)
                )
meta.create_all(bind=engine)