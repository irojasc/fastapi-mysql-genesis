from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, _Binary, Float, DateTime
from config.db import meta, engine
from datetime import datetime

Ware_Product = Table("ware_product", meta, 
                Column("idWare", Integer, nullable=False, unique=True, primary_key=True), 
                Column("idProduct", Integer, nullable=True),
                Column("qtyNew", Integer, nullable=False), 
                Column("qtyOld", Integer,  default=0), 
                Column("pvNew", Float, default=0),
                Column("pvOld", Float, default=0),
                Column("loc", String(20), nullable=True),
                Column("dsct", Float, default=0),
                Column("qtyMinimun", Integer, default=0),
                Column("isEnabled", _Binary, default=1),
                Column("editDate", DateTime, nullable=True),
                Column("creationDate", DateTime, nullable=True),
                Column("qtyMaximum", Integer, default=0)
                )
meta.create_all(bind=engine)