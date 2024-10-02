from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary
from config.db import meta, engine

Item = Table("item", meta, 
                Column("id", Integer, nullable=False, unique=True, primary_key=True), 
                Column("code", String(4), nullable=False), 
                Column("item", String(10), nullable=False), 
                )
meta.create_all(bind=engine)