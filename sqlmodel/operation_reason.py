from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String
from config.db import meta, engine

Operation_Reason = Table("operation_reason", meta, 
                Column("idOperReas", Integer, nullable=False, unique=True, primary_key=True), 
                Column("operation", String(15), nullable=False), 
                Column("reason", String(19), nullable=True, default=None),
                )
meta.create_all(bind=engine)