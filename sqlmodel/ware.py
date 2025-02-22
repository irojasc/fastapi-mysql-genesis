from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary
from config.db import meta, engine

Ware = Table("ware", meta, 
                Column("id", Integer, nullable=False, unique=True, primary_key=True),
                Column("warelvl", Integer, nullable=False, default=0), 
                Column("code", String(5), nullable=True), 
                Column("address", String(60), default=None), 
                Column("phone", String(12), default=None), 
                Column("isVirtual", _Binary, default=b'\x00'),
                Column("enabled", _Binary, default=b'\x01'), 
                Column("city", String(12), default=None), 
                Column("name", String(15), default=None),
                Column("isPos", _Binary, nullable=False, default=b'\x01'),
                )
meta.create_all(bind=engine)