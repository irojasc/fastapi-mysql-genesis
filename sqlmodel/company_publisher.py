from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String
from config.db import meta, engine

CompanyPublisher = Table("company_publisher", meta, 
                Column("doc", String(11), nullable=True), 
                Column("publisher", String(90), nullable=True), 
                )
meta.create_all(bind=engine)