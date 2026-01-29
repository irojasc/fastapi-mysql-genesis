from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary
from config.db import meta, engine

Language = Table("language", meta, 
                Column("id", Integer, nullable=False, unique=True, primary_key=True), 
                Column("code", String(10), nullable=False, unique=True),
                Column("language", String(20), nullable=False),
                )
meta.create_all(bind=engine)