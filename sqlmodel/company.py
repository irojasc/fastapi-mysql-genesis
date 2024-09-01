from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, Date, BINARY
from config.db import meta, engine

Company = Table("company", meta, 
                Column("doc", String(11), primary_key=True), 
                Column("docName", String(50), nullable=True), 
                Column("address", String(50), nullable=True), 
                Column("email", String(15), nullable=True), 
                Column("phone", String(15), nullable=True), 
                Column("idUbigeo", Integer, nullable=True),
                Column("active", BINARY, default=1), 
                Column("type", Date, default='S')
                )
meta.create_all(bind=engine)