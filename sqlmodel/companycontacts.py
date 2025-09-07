from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String, Integer
from config.db import meta, engine

CompanyContacts = Table("CompanyContacts", meta, 
                    Column("cardCode", String(20), primary_key=True), 
                    Column("LineId", Integer, primary_key=True), 
                    Column("Name", String(100), nullable=False),
                    Column("Phone", String(30), nullable=True),
                    Column("Email", String(100), nullable=True),
                    Column("DefaultContact", Integer, nullable=True, default=0)
                )
meta.create_all(bind=engine)