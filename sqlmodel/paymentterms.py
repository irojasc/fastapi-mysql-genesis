from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import  String, Integer
from config.db import meta, engine

PaymentTerms = Table("PaymentTerms", meta, 
                Column("TermCode", String(10), primary_key=True), 
                Column("TermName", String(100), nullable=False), 
                Column("PayType", String(2), nullable=True),
                Column("BaseDays", Integer, nullable=True),
                Column("WeekendOffset", Integer, nullable=True),
                Column("ConsignDays", Integer, nullable=True),
                Column("Times", Integer, nullable=True, default=1),
                Column("Active", String(1), nullable=True, default='Y')
                )
meta.create_all(bind=engine)