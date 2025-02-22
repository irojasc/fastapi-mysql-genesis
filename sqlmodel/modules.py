from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary
from config.db import meta, engine

Modules = Table("modules", meta, 
                Column("mdlCode", String(10), nullable=False, unique=True, primary_key=True), 
                Column("mdlName", String(50), nullable=False, unique=True), 
                )
meta.create_all(bind=engine)