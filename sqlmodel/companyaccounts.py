from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String, Integer
from config.db import meta, engine

CompanyAccounts = Table("CompanyAccounts", meta, 
                    Column("cardCode", String(15), primary_key=True), 
                    Column("LineId", Integer, primary_key=True), 
                    Column("AccountType", String(10), nullable=True),
                    Column("BankCodeApi", String(10), nullable=False),
                    Column("AccountNumber", String(30), nullable=True),
                    Column("InterbankNumber", String(30), nullable=True),
                    Column("AccountHolder", String(80), nullable=True)
                )
meta.create_all(bind=engine)