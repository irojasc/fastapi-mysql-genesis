from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, LargeBinary
from config.db import meta, engine

WareHouse = Table("ware", meta, 
                Column("id", Integer, nullable=False), 
                Column("warelvl", Integer, nullable=False), 
                Column("code", String(5), default=None), 
                Column("address", String(60), default=None), 
                Column("phone", String(12), default=None), 
                Column("isVirtual", LargeBinary, default=0), 
                Column("enabled", LargeBinary, default=1), 
                Column("city", String(12), default=None), 
                Column("name", String(15), default=None))

meta.create_all(bind=engine)