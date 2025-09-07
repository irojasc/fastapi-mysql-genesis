from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String
from config.db import meta, engine

Permissions = Table("permissions", meta, 
                Column("permCode", String(10), nullable=False, unique=True, primary_key=True), 
                Column("permName", String(50), nullable=False),
                Column("mdlCode", String(10), nullable=True),
                )
meta.create_all(bind=engine)