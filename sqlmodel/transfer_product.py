from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta, engine

Transfer_Product = Table("transfer_product", meta,
                Column("id", Integer, nullable=False, unique=True, primary_key=True),
                Column("idTransfer", String(12), nullable=False), 
                Column("idProduct", Integer, nullable=False, default=None), 
                Column("qtyNew", Integer, nullable=False, default=0), 
                Column("qtyOld", Integer, nullable=False, default=0)
                )
meta.create_all(bind=engine)