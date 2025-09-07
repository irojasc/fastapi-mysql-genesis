from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String
from config.db import meta, engine

Banks = Table("banks", meta, 
                Column("BankCodeApi", String(10), primary_key=True), 
                Column("BankCodeSbs", String(10), nullable=True), 
                Column("BankName", String(100), nullable=False)
                )
meta.create_all(bind=engine)