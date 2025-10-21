from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String
from config.db import meta, engine

PymntGroup = Table("PymntGroup", meta, 
                Column("PymntGroup", String(5), nullable=False, unique=True, primary_key=True), 
                Column("PymntGroupName", String(25), nullable=False), 
                )
meta.create_all(bind=engine)
