from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, BINARY, Boolean
from config.db import meta, engine

Company = Table("company", meta, 
                Column("cardCode", String(11), primary_key=True), 
                Column("docName", String(50), nullable=True), 
                Column("address", String(50), nullable=True), 
                Column("email", String(15), nullable=True), 
                Column("phone", String(15), nullable=True), 
                Column("idUbigeo", Integer, nullable=True),
                Column("active", BINARY, default=b'\x01'),
                Column("type", Date, default='S')
                )
meta.create_all(bind=engine)