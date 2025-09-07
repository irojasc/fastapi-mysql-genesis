from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta, engine

Ubigeo = Table("ubigeo", meta, 
                Column("idUbigeo", Integer, primary_key=True), 
                Column("pais", String(20), default='PERU'), 
                Column("dep_id", String(4), nullable=True, default=None), 
                Column("pro_id", String(4), nullable=True, default=None), 
                Column("dis_id", String(4), nullable=True, default=None), 
                Column("dep_name", String(25), nullable=True, default=None),
                Column("pro_name", String(25), nullable=True, default=None), 
                Column("dis_name", String(25), nullable=True, default=None)
                )
meta.create_all(bind=engine)