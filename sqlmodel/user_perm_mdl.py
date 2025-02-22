from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import String
from config.db import meta, engine

User_perm_mdl = Table("user_perm_mdl", meta, 
                Column("mdlCode", String(10), nullable=False, primary_key=True), 
                Column("permCode", String(10), nullable=False, primary_key=True), 
                Column("user", String(15), nullable=False, primary_key=True),
                )
meta.create_all(bind=engine)